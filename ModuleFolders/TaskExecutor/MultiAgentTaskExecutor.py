"""
多智能体任务执行器
集成多智能体工作流到现有任务执行系统
"""

import threading
import time
from Base.Base import Base
from ModuleFolders.TaskConfig.TaskConfig import TaskConfig
from ModuleFolders.TaskConfig.TaskType import TaskType
from ModuleFolders.MultiAgent.WorkflowManager import WorkflowManager
from ModuleFolders.Cache.CacheManager import CacheManager
from ModuleFolders.Cache.CacheProject import CacheProjectStatistics
from ModuleFolders.FileOutputer.FileOutputer import FileOutputer


class MultiAgentTaskExecutor(Base):
    """
    多智能体任务执行器
    使用WorkflowManager执行基于Agent的翻译工作流
    """
    
    def __init__(self, cache_manager: CacheManager, file_writer: FileOutputer):
        super().__init__()
        self.cache_manager = cache_manager
        self.file_writer = file_writer
        self.config = TaskConfig()
        self.workflow_manager = None
        
        # 注册事件
        self.subscribe(Base.EVENT.TASK_START, self.task_start)
        self.subscribe(Base.EVENT.TASK_STOP, self.task_stop)
        self.subscribe(Base.EVENT.APP_SHUT_DOWN, self.app_shut_down)
    
    def _update_stage_progress(self, cache_project, stage: str, current: int, total: int):
        """更新当前阶段的进度信息（用于预估时间）"""
        import time
        
        if not cache_project.stats_data:
            return
        
        with cache_project.stats_data.atomic_scope():
            # 如果是新阶段，重置阶段开始时间
            if cache_project.stats_data.current_stage != stage:
                cache_project.stats_data.current_stage = stage
                cache_project.stats_data.stage_start_time = time.time()
                self.debug(f"[MultiAgentTaskExecutor] 进入新阶段: {stage}, 总进度={total}")
            
            # 更新进度
            cache_project.stats_data.stage_progress_current = current
            cache_project.stats_data.stage_progress_total = total
    
    def _publish_stage_with_stats(self, cache_project, stage: str, batch_info: str):
        """发送包含统计数据的阶段更新（与WorkflowManager保持一致）"""
        import time
        
        # 🔥 使用atomic_scope确保读取最新的统计数据
        if cache_project.stats_data:
            with cache_project.stats_data.atomic_scope():
                # 🔥 更新已消耗时间（确保阶段更新时也同步时间）
                cache_project.stats_data.time = time.time() - cache_project.stats_data.start_time
                update_data = cache_project.stats_data.to_dict()
        else:
            update_data = {}
        
        # 添加阶段信息
        update_data["agent_stage"] = {
            "stage": stage,
            "batch_info": batch_info
        }
        
        self.debug(f"[MultiAgentTaskExecutor] 发送阶段更新: stage={stage}, batch_info={batch_info}, line={update_data.get('line', 0)}/{update_data.get('total_line', 0)}, time={update_data.get('time', 0):.1f}s")
        self.emit(Base.EVENT.TASK_UPDATE, update_data)
    
    def task_start(self, event: int, data: dict) -> None:
        """任务开始事件处理"""
        continue_status = data.get("continue_status", False)
        current_mode = data.get("current_mode")
        use_multi_agent = data.get("use_multi_agent", False)  # 是否使用多智能体模式
        
        # 如果启用多智能体模式，使用新的工作流
        if use_multi_agent and current_mode == TaskType.TRANSLATION:
            threading.Thread(
                target=self.multi_agent_translation_start,
                args=(continue_status,),
                daemon=True
            ).start()
        else:
            # 否则使用原有的TaskExecutor（这里需要确保原有系统仍然可用）
            self.info("使用传统翻译模式（非多智能体）")
    
    def multi_agent_translation_start(self, continue_status: bool) -> None:
        """
        多智能体翻译主流程
        """
        # 设置翻译状态
        Base.work_status = Base.STATUS.TASKING
        
        # 初始化配置
        self.config.initialize()
        self.config.prepare_for_translation(TaskType.TRANSLATION)
        
        # 初始化工作流管理器
        self.workflow_manager = WorkflowManager(self.config)
        
        # 加载缓存项目
        if not hasattr(self.cache_manager, "project") or not self.cache_manager.project:
            self.error("未找到缓存项目，请先加载文件")
            Base.work_status = Base.STATUS.TASKSTOPPED
            self.emit(Base.EVENT.TASK_STOP_DONE, {})
            return
        
        cache_project = self.cache_manager.project
        
        # 初始化项目统计数据（类似TaskExecutor的做法）
        if not continue_status:
            # 开始新翻译时，创建新的统计数据
            project_status_data = CacheProjectStatistics()
            self.cache_manager.project.stats_data = project_status_data
        else:
            # 继续翻译时，使用已有的统计数据
            if self.cache_manager.project.stats_data:
                project_status_data = self.cache_manager.project.stats_data
                project_status_data.start_time = time.time()  # 重置开始时间
                project_status_data.total_completion_tokens = 0  # 重置完成的token数量
            else:
                # 如果继续翻译但stats_data为空，创建新的
                project_status_data = CacheProjectStatistics()
                self.cache_manager.project.stats_data = project_status_data
        
        # 如果是继续翻译，从文件加载
        if continue_status:
            config = self.load_config()
            output_path = config.get("label_output_path", "./output")
            if output_path:
                self.cache_manager.load_from_file(output_path)
                cache_project = self.cache_manager.project
        
        self.info("=" * 60)
        self.info("开始执行多智能体翻译工作流")
        self.info("=" * 60)
        
        # 初始化统计数据的总行数
        from ModuleFolders.Cache.CacheItem import TranslationStatus
        total_line = sum(
            1 for _ in cache_project.items_iter() 
            if _.translation_status == TranslationStatus.UNTRANSLATED
        )
        project_status_data.total_line = total_line
        project_status_data.line = 0
        project_status_data.start_time = time.time()
        
        # 发送初始进度事件
        self.emit(Base.EVENT.TASK_UPDATE, project_status_data.to_dict())
        
        # 定义进度更新回调函数
        def progress_callback(current: int, total: int, stage: str, message: str = ""):
            """
            进度更新回调
            
            Args:
                current: 当前完成数
                total: 总数
                stage: 当前阶段
                message: 附加消息
            """
            with project_status_data.atomic_scope():
                project_status_data.line = current
                project_status_data.total_line = total
                project_status_data.time = time.time() - project_status_data.start_time
                stats_dict = project_status_data.to_dict()
                stats_dict["stage"] = stage
                stats_dict["message"] = message
            
            # 触发进度更新事件
            self.emit(Base.EVENT.TASK_UPDATE, stats_dict)
            
            # 同时发送Agent流程事件（用于Agent流程展示界面）
            self.emit(Base.EVENT.AGENT_FLOW_UPDATE, {
                "stage": stage,
                "progress": current / total if total > 0 else 0,
                "message": message,
                "current": current,
                "total": total
            })
        
        # 定义人工介入回调函数
        def human_intervention_callback(task_type: str, task_data: dict):
            """
            人工介入回调
            确保在GUI线程中阻塞执行
            """
            from PyQt5.QtCore import QObject, pyqtSignal, Qt, QEventLoop
            from PyQt5.QtWidgets import QApplication
            from ModuleFolders.MultiAgent.HumanCollaborationNode import HumanCollaborationNode
            import threading
            
            # 结果容器
            result_container = {"data": None}
            
            # 定义一个专门的信号发射器类（必须在方法内定义或外部定义）
            class Invoker(QObject):
                # 信号携带参数：task_type, task_data
                invoke_signal = pyqtSignal(str, dict)
                
                def __init__(self):
                    super().__init__()
                    self.human_collab = HumanCollaborationNode()
                
                def run(self, t_type, t_data):
                    try:
                        # 获取主窗口
                        parent_widget = None
                        app = QApplication.instance()
                        if app:
                            for widget in app.topLevelWidgets():
                                if hasattr(widget, 'windowTitle') and widget.isVisible():
                                    parent_widget = widget
                                    break
                        
                        # 执行
                        result_container["data"] = self.human_collab.request_human_input(
                            t_type, t_data, parent_widget
                        )
                    except Exception as e:
                        print(f"人工介入UI错误: {e}")
            
            app = QApplication.instance()
            if not app:
                return None
            
            # 如果已经在主线程
            if threading.current_thread() is threading.main_thread():
                invoker = Invoker()
                invoker.run(task_type, task_data)
                return result_container["data"]
            
            # 在工作线程：使用 BlockingQueuedConnection
            # 1. 创建Invoker并移动到主线程
            invoker = Invoker()
            invoker.moveToThread(app.thread())
            
            # 2. 连接信号到槽
            invoker.invoke_signal.connect(invoker.run, Qt.BlockingQueuedConnection)
            
            # 3. 发射信号（这将阻塞直到槽函数返回）
            # 注意：发射信号的线程和槽所在的线程不同，且使用了BlockingQueuedConnection
            invoker.invoke_signal.emit(task_type, task_data)
            
            return result_container["data"]
        
        try:
            # 执行工作流
            workflow_result = self.workflow_manager.execute_workflow(
                cache_project=cache_project,
                human_intervention_callback=human_intervention_callback,
                progress_callback=progress_callback
            )
            
            if workflow_result.get("success"):
                # 更新缓存项目
                self.cache_manager.project = workflow_result["cache_project"]
                cache_project = self.cache_manager.project
                
                # 🔥 发送UI阶段更新：保存阶段
                file_count = len(cache_project.files) if cache_project.files else 1
                self._update_stage_progress(cache_project, "saving", 0, file_count)
                self._publish_stage_with_stats(cache_project, "saving", "保存中")
                
                # 保存缓存
                config = self.load_config()
                output_path = config.get("label_output_path", "./output")
                if output_path:
                    self.cache_manager.require_save_to_file(output_path)
                
                # 输出文件到项目独立目录
                project_output_path = self.cache_manager.get_project_output_directory(
                    self.config.label_output_path
                )
                
                output_config = {
                    "translated_suffix": self.config.output_filename_suffix,
                    "bilingual_suffix": "_bilingual",
                    "bilingual_order": self.config.bilingual_text_order
                }
                
                self.info(f"翻译文件将输出到项目目录: {project_output_path}")
                
                self.file_writer.output_translated_content(
                    self.cache_manager.project,
                    project_output_path,  # 使用项目独立目录
                    self.config.label_input_path,
                    output_config
                )
                
                # 🔥 更新保存进度：完成
                self._update_stage_progress(cache_project, "saving", file_count, file_count)
                
                self.info("=" * 60)
                self.info("多智能体翻译工作流执行完成")
                self.info("=" * 60)
                
                # 🔥 发送UI阶段更新：已完成
                self._update_stage_progress(cache_project, "completed", 1, 1)
                self._publish_stage_with_stats(cache_project, "completed", "")
                
                # 触发完成事件
                self.emit(Base.EVENT.TASK_COMPLETED, {})
            else:
                self.error("多智能体翻译工作流执行失败")
                error = workflow_result.get("error", "未知错误")
                self.error(f"错误详情: {error}")
        
        except Exception as e:
            self.error(f"多智能体翻译执行异常: {e}", e)
        
        finally:
            # 重置状态
            Base.work_status = Base.STATUS.TASKSTOPPED
            self.emit(Base.EVENT.TASK_STOP_DONE, {})
    
    def task_stop(self, event: int, data: dict) -> None:
        """任务停止事件处理"""
        Base.work_status = Base.STATUS.STOPING
    
    def app_shut_down(self, event: int, data: dict) -> None:
        """应用关闭事件处理"""
        Base.work_status = Base.STATUS.STOPING
