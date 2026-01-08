"""
Agent流程展示页面
用于可视化多智能体工作流的执行状态
"""

import threading
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from qfluentwidgets import (
    CardWidget, ProgressBar, FluentIcon as FIF,
    SubtitleLabel, BodyLabel, CaptionLabel,
    FlowLayout
)

from Base.Base import Base


class AgentFlowCard(CardWidget):
    """单个Agent状态卡片"""
    
    def __init__(self, agent_name: str, agent_desc: str, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.agent_desc = agent_desc
        self.status = "pending"  # pending, running, completed, failed
        self.progress = 0.0
        self.message = ""
        
        self.setFixedSize(280, 180)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题行（Agent名称 + 状态图标）
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        self.title_label = SubtitleLabel(self.agent_name)
        self.title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        
        self.status_icon = QLabel("●")
        self.status_icon.setFont(QFont("Arial", 16))
        self.update_status_color()
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.status_icon)
        
        # 描述
        self.desc_label = CaptionLabel(self.agent_desc)
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumHeight(40)
        
        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        
        # 状态消息
        self.message_label = BodyLabel(self.message or "等待执行...")
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(30)
        
        layout.addLayout(title_layout)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.message_label)
        layout.addStretch()
    
    def update_status(self, status: str, progress: float = 0.0, message: str = ""):
        """更新Agent状态"""
        self.status = status
        self.progress = progress
        self.message = message
        
        self.update_status_color()
        self.progress_bar.setValue(int(progress * 100))
        self.message_label.setText(message or self._get_status_text())
    
    def update_status_color(self):
        """更新状态颜色"""
        colors = {
            "pending": "#808080",  # 灰色
            "running": "#0078D4",  # 蓝色
            "completed": "#16C60C",  # 绿色
            "failed": "#E81123",  # 红色
        }
        color = colors.get(self.status, "#808080")
        self.status_icon.setStyleSheet(f"color: {color};")
    
    def _get_status_text(self):
        """获取状态文本"""
        texts = {
            "pending": "等待执行...",
            "running": "执行中...",
            "completed": "✓ 执行完成",
            "failed": "✗ 执行失败"
        }
        return texts.get(self.status, "")


class AgentFlowPage(Base, QWidget):
    """Agent流程展示页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_cards = {}
        self.setup_ui()
        
        # 注册事件
        self.subscribe(Base.EVENT.AGENT_FLOW_UPDATE, self.update_agent_flow)
        self.subscribe(Base.EVENT.TASK_START, self.on_task_start)
        self.subscribe(Base.EVENT.TASK_COMPLETED, self.on_task_completed)
        self.subscribe(Base.EVENT.TASK_STOP_DONE, self.on_task_stop)
    
    def setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = SubtitleLabel(self.tra("多智能体工作流"))
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Agent卡片容器
        self.card_container = QWidget(self)
        self.card_layout = FlowLayout(self.card_container, needAni=False)
        self.card_layout.setSpacing(16)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建Agent卡片
        self.create_agent_cards()
        
        main_layout.addWidget(self.card_container)
        main_layout.addStretch()
    
    def create_agent_cards(self):
        """创建Agent卡片"""
        agents = [
            {
                "name": "PlanningAgent",
                "display_name": self.tra("规划Agent"),
                "description": self.tra("任务分析与规划")
            },
            {
                "name": "PreprocessingAgent",
                "display_name": self.tra("预处理Agent"),
                "description": self.tra("文本预处理与结构化")
            },
            {
                "name": "TerminologyAgent",
                "display_name": self.tra("术语Agent"),
                "description": self.tra("术语与实体识别")
            },
            {
                "name": "TranslationAgent",
                "display_name": self.tra("翻译Agent"),
                "description": self.tra("多步骤翻译与优化")
            },
        ]
        
        for agent_info in agents:
            card = AgentFlowCard(
                agent_info["display_name"],
                agent_info["description"],
                self.card_container
            )
            self.agent_cards[agent_info["name"]] = card
            self.card_layout.addWidget(card)
    
    def update_agent_flow(self, event: int, data: dict):
        """更新Agent流程"""
        stage = data.get("stage", "")
        progress = data.get("progress", 0.0)
        message = data.get("message", "")
        
        # 映射stage到Agent名称
        stage_to_agent = {
            "planning": "PlanningAgent",
            "preprocessing": "PreprocessingAgent",
            "preprocess": "PreprocessingAgent",
            "terminology": "TerminologyAgent",
            "translation": "TranslationAgent",
            "translate": "TranslationAgent",
        }
        
        agent_name = stage_to_agent.get(stage)
        if agent_name and agent_name in self.agent_cards:
            card = self.agent_cards[agent_name]
            
            # 根据进度判断状态
            if progress >= 1.0:
                status = "completed"
            elif progress > 0:
                status = "running"
            else:
                status = "running"  # 刚开始
            
            card.update_status(status, progress, message)
            
            # 更新前面的Agent为完成状态
            agents_order = ["PlanningAgent", "PreprocessingAgent", "TerminologyAgent", "TranslationAgent"]
            current_index = agents_order.index(agent_name) if agent_name in agents_order else -1
            for i, prev_agent in enumerate(agents_order):
                if i < current_index:
                    self.agent_cards[prev_agent].update_status("completed", 1.0)
    
    def on_task_start(self, event: int, data: dict):
        """任务开始事件"""
        use_multi_agent = data.get("use_multi_agent", False)
        if not use_multi_agent:
            return
        
        # 重置所有Agent状态
        for card in self.agent_cards.values():
            card.update_status("pending", 0.0, "等待执行...")
        
        self.info("多智能体工作流开始执行")
    
    def on_task_completed(self, event: int, data: dict):
        """任务完成事件"""
        # 标记所有Agent为完成
        for card in self.agent_cards.values():
            if card.status == "running" or card.status == "pending":
                card.update_status("completed", 1.0, "✓ 执行完成")
        
        self.info("多智能体工作流执行完成")
    
    def on_task_stop(self, event: int, data: dict):
        """任务停止事件"""
        # 标记未完成的Agent为失败
        for card in self.agent_cards.values():
            if card.status == "running" or card.status == "pending":
                card.update_status("failed", card.progress, "✗ 已停止")
        
        self.info("多智能体工作流已停止")

