import threading
import time
from PyQt5.QtWidgets import QLayout, QWidget, QVBoxLayout
from qfluentwidgets import (FlowLayout,FluentIcon as FIF)

from Base.Base import Base
from Widget.DashboardCard import DashboardCard
from Widget.ProgressRingCard import ProgressRingCard
from Widget.CombinedLineCard import CombinedLineCard

# 监控页面
class MonitoringPage(Base,QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置主容器
        self.container = QVBoxLayout(self)
        self.container.setSpacing(8)
        self.container.setContentsMargins(24, 24, 24, 24)  # 左、上、右、下

        # 添加控件
        self.head_hbox_container = QWidget(self)
        self.head_hbox = FlowLayout(self.head_hbox_container, needAni=False)
        self.head_hbox.setSpacing(8)
        self.head_hbox.setContentsMargins(0, 0, 0, 0)

        # 添加卡片控件
        self.add_combined_line_card(self.head_hbox)
        self.add_time_card(self.head_hbox)
        self.add_remaining_time_card(self.head_hbox)
        self.add_token_card(self.head_hbox)
        self.add_task_card(self.head_hbox)
        self.add_ring_card(self.head_hbox)
        self.add_speed_card(self.head_hbox)
        self.add_agent_stage_card(self.head_hbox)  # 🆕 多Agent翻译阶段

        # 添加到主容器
        self.container.addWidget(self.head_hbox_container, 1)

        # 注册事件
        self.subscribe(Base.EVENT.TASK_UPDATE, self.data_update) # 监听监控数据更新事件
        self.subscribe(Base.EVENT.TASK_COMPLETED, self.data_update)  # 监听任务完成事件

        # 监控页面数据存储
        self.data = {}


    # 进度环
    def add_ring_card(self, parent: QLayout) -> None:
        self.ring = ProgressRingCard(title=self.tra("任务进度"),
                    icon=FIF.PIE_SINGLE,
                    min_value=0,
                    max_value=10000,
                    ring_size=(140, 140),
                    text_visible=True)
        self.ring.setFixedSize(204, 204)
        self.ring.set_format(self.tra("无任务"))
        parent.addWidget(self.ring)


    # 累计时间
    def add_time_card(self, parent: QLayout) -> None:
        self.time = DashboardCard(
                title=self.tra("累计时间"),
                value="Time",
                unit="",
                icon=FIF.STOP_WATCH,
            )
        self.time.setFixedSize(204, 204)
        parent.addWidget(self.time)

    # 剩余时间
    def add_remaining_time_card(self, parent: QLayout) -> None:
        self.remaining_time = DashboardCard(
                title=self.tra("剩余时间"),
                value="Time",
                unit="",
                icon=FIF.FRIGID,
            )
        self.remaining_time.setFixedSize(204, 204)
        parent.addWidget(self.remaining_time)

    # 行数统计
    def add_combined_line_card(self, parent: QLayout) -> None:

        self.combined_line_card = CombinedLineCard(
            title=self.tra("行数统计"),
            icon=FIF.PRINT,
            left_title=self.tra("已完成"),
            right_title=self.tra("剩余"),
            initial_left_value="0",
            initial_left_unit="Line",
            initial_right_value="0",
            initial_right_unit="Line",
            parent=self
        )

        self.combined_line_card.setFixedSize(416, 204)
        parent.addWidget(self.combined_line_card)

    # 平均速度
    def add_speed_card(self, parent: QLayout) -> None:
        self.speed = DashboardCard(
                title=self.tra("平均速度"),
                value="T/S",
                unit="",
                icon=FIF.SPEED_HIGH,
            )
        self.speed.setFixedSize(204, 204)
        parent.addWidget(self.speed)

    # 累计消耗
    def add_token_card(self, parent: QLayout) -> None:
        self.token = DashboardCard(
                title=self.tra("累计消耗"),
                value="Token",
                unit="",
                icon=FIF.CALORIES,
            )
        self.token.setFixedSize(204, 204)
        parent.addWidget(self.token)

    # 并行任务
    def add_task_card(self, parent: QLayout) -> None:
        self.task = DashboardCard(
                title=self.tra("实时任务数"),
                value="0",
                unit="",
                icon=FIF.SCROLL,
            )
        self.task.setFixedSize(204, 204)
        parent.addWidget(self.task)

    # 多Agent翻译阶段
    def add_agent_stage_card(self, parent: QLayout) -> None:
        self.agent_stage = DashboardCard(
                title=self.tra("翻译阶段"),
                value=self.tra("未开始"),
                unit="",
                icon=FIF.ROBOT,
            )
        self.agent_stage.setFixedSize(416, 204)
        parent.addWidget(self.agent_stage)


    # 监控页面更新事件
    def data_update(self, event: int, data: dict) -> None:
        # 🔥 总是更新阶段信息（不受work_status限制）
        self.update_agent_stage(event, data)
        
        if Base.work_status in (Base.STATUS.STOPING, Base.STATUS.TASKING):
            self.update_time(event, data)
            self.update_line(event, data)
            self.update_token(event, data)

        self.update_task(event, data)
        self.update_status(event, data)

    # 更新时间
    def update_time(self, event: int, data: dict) -> None:
        if data.get("start_time", None) is not None:
            self.data["start_time"] = data.get("start_time")
            self.debug(f"[MonitoringPage] 接收到start_time: {data.get('start_time', 0):.0f}")

        if self.data.get("start_time", 0) == 0:
            total_time = 0
            # 只在第一次打印
            if not hasattr(self, '_warned_no_start_time'):
                self.debug(f"[MonitoringPage] start_time未初始化，total_time=0")
                self._warned_no_start_time = True
        else:
            total_time = int(time.time() - self.data.get("start_time", 0))

        if total_time < 60:
            self.time.set_unit("S")
            self.time.set_value(f"{total_time}")
        elif total_time < 60 * 60:
            self.time.set_unit("M")
            self.time.set_value(f"{(total_time / 60):.2f}")
        else:
            self.time.set_unit("H")
            self.time.set_value(f"{(total_time / 60 / 60):.2f}")

        # 🔥 计算剩余时间（使用阶段进度，而不是completed_lines）
        remaining_time = self._calculate_remaining_time_by_stage(data, total_time)
        
        if remaining_time < 60:
            self.remaining_time.set_unit("S")
            self.remaining_time.set_value(f"{remaining_time}")
        elif remaining_time < 60 * 60:
            self.remaining_time.set_unit("M")
            self.remaining_time.set_value(f"{(remaining_time / 60):.2f}")
        else:
            self.remaining_time.set_unit("H")
            self.remaining_time.set_value(f"{(remaining_time / 60 / 60):.2f}")

    def _calculate_remaining_time_by_stage(self, data: dict, total_time: int) -> int:
        """
        根据当前阶段进度和行数计算预估剩余时间
        
        策略：
        1. 优先使用行数计算（最准确）
        2. 如果行数为0，使用阶段进度 + 行数权重估算
        
        Args:
            data: 统计数据
            total_time: 已消耗的总时间
            
        Returns:
            预估剩余时间（秒）
        """
        # 🔥 先保存所有字段到self.data（避免闪烁）
        if data.get("stage_progress_current", None) is not None:
            self.data["stage_progress_current"] = data.get("stage_progress_current")
        if data.get("stage_progress_total", None) is not None:
            self.data["stage_progress_total"] = data.get("stage_progress_total")
        if data.get("stage_start_time", None) is not None:
            self.data["stage_start_time"] = data.get("stage_start_time")
        if data.get("current_stage", None) is not None:
            self.data["current_stage"] = data.get("current_stage")
        
        # 🔥 从self.data读取
        stage_progress_current = self.data.get("stage_progress_current", 0)
        stage_progress_total = self.data.get("stage_progress_total", 0)
        stage_start_time = self.data.get("stage_start_time", 0)
        current_stage = self.data.get("current_stage", "")
        completed_lines = self.data.get("line", 0)
        total_lines = self.data.get("total_line", 0)
        
        # 🔥 策略1：如果已经开始翻译（有行数数据），使用行数计算（最准确）
        if completed_lines > 0 and total_lines > 0:
            remaining_lines = max(0, total_lines - completed_lines)
            # 基于行数的预估
            line_based_remaining = int(total_time / completed_lines * remaining_lines)
            
            # 每10次更新打印一次日志
            if not hasattr(self, '_time_update_count'):
                self._time_update_count = 0
            self._time_update_count += 1
            if self._time_update_count % 10 == 1:
                self.debug(f"[MonitoringPage] 基于行数预估: completed={completed_lines}/{total_lines}, remaining_time={line_based_remaining}s")
            
            return max(0, line_based_remaining)
        
        # 🔥 策略2：翻译前阶段，使用阶段进度 + 行数权重估算
        if stage_progress_total > 0 and total_lines > 0:
            # 当前阶段进度比例
            stage_progress_ratio = stage_progress_current / stage_progress_total if stage_progress_total > 0 else 0
            
            # 🔥 定义阶段顺序和每行消耗时间的权重
            # 假设翻译1行需要1个单位时间，其他阶段按行数比例分配
            stage_order = ["planning", "preprocessing", "terminology", "translating", "backtranslation", "entity_check", "saving"]
            stage_time_per_line = {
                "planning": 0.01,        # 每行0.01秒（总共约0.01*total_lines秒）
                "preprocessing": 0.02,   # 每行0.02秒
                "terminology": 0.05,     # 每行0.05秒
                "translating": 1.0,      # 每行1秒（基准）
                "backtranslation": 0.3,  # 每行0.3秒
                "entity_check": 0.1,     # 每行0.1秒
                "saving": 0.02,          # 每行0.02秒
            }
            
            # 计算总的"行-时间单位"
            total_line_time_units = sum(stage_time_per_line.get(s, 0) * total_lines for s in stage_order)
            
            # 计算已完成的"行-时间单位"
            completed_line_time_units = 0.0
            for stage in stage_order:
                if stage == current_stage:
                    # 当前阶段：部分完成
                    completed_line_time_units += stage_time_per_line.get(stage, 0) * total_lines * stage_progress_ratio
                    break
                else:
                    # 之前的阶段：全部完成
                    completed_line_time_units += stage_time_per_line.get(stage, 0) * total_lines
            
            # 剩余的"行-时间单位"
            remaining_line_time_units = max(0, total_line_time_units - completed_line_time_units)
            
            # 估算剩余时间
            if completed_line_time_units > 0 and total_time > 0:
                time_per_unit = total_time / completed_line_time_units
                remaining_time = int(time_per_unit * remaining_line_time_units)
            else:
                # 🔥 如果还没有足够数据，使用阶段内部进度估算
                if stage_start_time > 0 and stage_progress_current > 0 and stage_progress_total > 0:
                    # 有当前阶段的进度数据
                    stage_elapsed = time.time() - stage_start_time
                    stage_remaining_progress = stage_progress_total - stage_progress_current
                    remaining_time = int(stage_elapsed / stage_progress_current * stage_remaining_progress)
                    # 加上后续阶段的粗略估算（假设每个后续阶段平均10秒）
                    current_stage_idx = stage_order.index(current_stage) if current_stage in stage_order else 0
                    remaining_stages = len(stage_order) - current_stage_idx - 1
                    remaining_time += remaining_stages * 10
                elif total_lines > 0:
                    # 🔥 刚开始阶段，没有历史数据，使用基于总行数的粗略估算
                    # 使用剩余的"行-时间单位"和一个假设的平均速度（如每个单位1秒）
                    remaining_time = int(remaining_line_time_units)  # 假设每个时间单位=1秒
                else:
                    remaining_time = 0
            
            # 每10次更新打印一次日志
            if not hasattr(self, '_time_update_count'):
                self._time_update_count = 0
            self._time_update_count += 1
            if self._time_update_count % 10 == 1:
                self.debug(f"[MonitoringPage] 基于阶段+行数预估: stage={current_stage}, progress={stage_progress_current}/{stage_progress_total}, total_lines={total_lines}, remaining_time={remaining_time}s")
            
            return max(0, remaining_time)
        
        # 🔥 Fallback：如果没有total_lines数据，无法预估
        if not hasattr(self, '_warned_no_progress'):
            self.debug(f"[MonitoringPage] 无法计算预估时间：缺少total_lines数据")
            self._warned_no_progress = True
        return 0

    # 更新行数
    def update_line(self, event: int, data: dict) -> None:
        if data.get("line", None) is not None and data.get("total_line", None) is not None:
            self.data["line"] = data.get("line")
            self.data["total_line"] = data.get("total_line")

        translated_line = self.data.get("line", 0)
        total_line = self.data.get("total_line", 0)
        remaining_line = max(0, total_line - translated_line)

        t_value_str: str
        t_unit_str: str
        if translated_line < 1000:
            t_unit_str = "Line"
            t_value_str = f"{translated_line}"
        elif translated_line < 1000 * 1000:
            t_unit_str = "KLine"
            t_value_str = f"{(translated_line / 1000):.2f}"
        else:
            t_unit_str = "MLine"
            t_value_str = f"{(translated_line / 1000 / 1000):.2f}"

        r_value_str: str
        r_unit_str: str
        if remaining_line < 1000:
            r_unit_str = "Line"
            r_value_str = f"{remaining_line}"
        elif remaining_line < 1000 * 1000:
            r_unit_str = "KLine"
            r_value_str = f"{(remaining_line / 1000):.2f}"
        else:
            r_unit_str = "MLine"
            r_value_str = f"{(remaining_line / 1000 / 1000):.2f}"

        if hasattr(self, 'combined_line_card') and self.combined_line_card:
            self.combined_line_card.set_left_data(value=t_value_str, unit=t_unit_str)
            self.combined_line_card.set_right_data(value=r_value_str, unit=r_unit_str)

    # 更新实时LLM调用数
    def update_task(self, event: int, data: dict) -> None:
        # 🔥 先保存到self.data（与update_line、update_token保持一致）
        if data.get("active_llm_calls", None) is not None:
            self.data["active_llm_calls"] = data.get("active_llm_calls")
        
        # 🔥 从self.data读取（避免闪烁）
        llm_count = self.data.get("active_llm_calls", 0)
        
        # 如果没有传入，仍然使用线程数作为fallback
        if llm_count == 0:
            llm_count = len([t for t in threading.enumerate() if "translator" in t.name])
        
        if llm_count < 1000:
            self.task.set_unit("LLM")
            self.task.set_value(f"{llm_count}")
        else:
            self.task.set_unit("KLLM")
            self.task.set_value(f"{(llm_count / 1000):.2f}")

    # 更新 Token 数据和平均速度
    def update_token(self, event: int, data: dict) -> None:
        if data.get("token", None) is not None and data.get("total_completion_tokens", None) is not None:
            self.data["token"] = data.get("token")
            self.data["total_completion_tokens"] = data.get("total_completion_tokens")

        token = self.data.get("token", 0)
        if token < 1000:
            self.token.set_unit("Token")
            self.token.set_value(f"{token}")
        elif token < 1000 * 1000:
            self.token.set_unit("KToken")
            self.token.set_value(f"{(token / 1000):.2f}")
        else:
            self.token.set_unit("MToken")
            self.token.set_value(f"{(token / 1000 / 1000):.2f}")

        # 🔥 改为按行速度计算（行/分钟）
        elapsed_time = max(1, time.time() - self.data.get("start_time", 0))
        completed_lines = self.data.get("line", 0)
        speed_per_min = (completed_lines / elapsed_time) * 60  # 行/分钟
        
        if speed_per_min < 1:
            self.speed.set_unit("行/小时")
            self.speed.set_value(f"{(speed_per_min * 60):.2f}")
        elif speed_per_min < 60:
            self.speed.set_unit("行/分")
            self.speed.set_value(f"{speed_per_min:.2f}")
        else:
            self.speed.set_unit("行/秒")
            self.speed.set_value(f"{(speed_per_min / 60):.2f}")

    # 更新Agent翻译阶段
    def update_agent_stage(self, event: int, data: dict) -> None:
        # 🔥 只有当数据中包含agent_stage字段时才更新，否则保持当前显示
        if "agent_stage" not in data:
            return
        
        stage_info = data.get("agent_stage", {})
        stage = stage_info.get("stage", "")
        batch_info = stage_info.get("batch_info", "")
        
        # 🔥 调试：打印接收到的数据
        if stage or batch_info:
            print(f"[UI接收] 阶段更新: stage={stage}, batch_info={batch_info}")
        
        # 阶段映射
        stage_map = {
            "planning": self.tra("任务规划"),
            "preprocessing": self.tra("文件处理"),
            "terminology": self.tra("实体识别"),
            "translating": self.tra("批量翻译"),
            "backtranslation": self.tra("回译评估"),
            "quality_check": self.tra("质量评估"),
            "entity_check": self.tra("一致性检查"),
            "refinement": self.tra("修正优化"),
            "saving": self.tra("翻译保存"),
            "completed": self.tra("已完成")
        }
        
        stage_text = stage_map.get(stage, self.tra("进行中"))
        
        # 🔥 调试：打印映射后的文本
        if stage:
            print(f"[UI更新] 显示文本: {stage_text} | {batch_info}")
        
        # 组合显示文本
        if batch_info:
            display_text = f"{stage_text}"
            self.agent_stage.set_value(display_text)
            self.agent_stage.set_unit(batch_info)
        else:
            self.agent_stage.set_value(stage_text)
            self.agent_stage.set_unit("")

    # 更新进度环
    def update_status(self, event: int, data: dict) -> None:
        if Base.work_status == Base.STATUS.STOPING:
            percent = self.data.get("line", 0) / max(1, self.data.get("total_line", 0))
            self.ring.set_value(int(percent * 10000))
            info_cont = self.tra("停止中") + "\n" + f"{percent * 100:.2f}%"
            self.ring.set_format(info_cont)
        elif Base.work_status == Base.STATUS.TASKING:
            percent = self.data.get("line", 0) / max(1, self.data.get("total_line", 0))
            self.ring.set_value(int(percent * 10000))
            info_cont = self.tra("任务中") + "\n" + f"{percent * 100:.2f}%"
            self.ring.set_format(info_cont)
        else:
            self.ring.set_value(0)
            info_cont = self.tra("无任务")
            self.ring.set_format(info_cont)

