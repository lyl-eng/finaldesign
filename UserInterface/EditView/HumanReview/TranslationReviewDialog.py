"""
批量回译审核对话框
用于展示所有回译评分未通过的行，允许用户进行人工审核
"""

from typing import List, Dict, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                              QTableWidgetItem, QPushButton, QLabel, QTextEdit,
                              QHeaderView, QWidget, QScrollArea, QFrame, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from qfluentwidgets import (PushButton, TextEdit, TitleLabel, BodyLabel, 
                            MessageBox, FluentIcon as FIF)
from Base.Base import Base


class TranslationReviewDialog(Base, QDialog):
    """
    批量回译审核对话框
    展示所有需要审核的翻译行，用户可以逐个审核
    """
    
    # 定义信号：审核完成信号，传递审核结果列表
    reviewFinished = pyqtSignal(list)  # List[Dict]
    
    def __init__(self, review_items: List[Dict], parent=None):
        """
        初始化审核对话框
        
        Args:
            review_items: 需要审核的项目列表，格式：
                [{
                    "index": 行索引,
                    "source_text": 原文,
                    "translated_text": 译文,
                    "back_translation": 回译,
                    "score": 评分,
                    "context_before": 上文（可选）,
                    "context_after": 下文（可选）
                }]
        """
        super().__init__(parent)
        
        self.review_items = review_items
        self.current_item_index = 0
        self.review_results = []  # 存储用户的审核决策
        
        self._init_ui()
        self._show_current_item()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"人工审核 - {len(self.review_items)} 行待审核")
        self.setMinimumSize(1000, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 顶部：标题和进度 ==========
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = TitleLabel("回译质量审核")
        self.progress_label = BodyLabel(f"当前: 1/{len(self.review_items)}")
        self.progress_label.setStyleSheet("font-size: 14px; color: #666;")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        
        main_layout.addWidget(header_widget)
        
        # ========== 中部：内容展示区域（使用Splitter分隔） ==========
        content_splitter = QSplitter(Qt.Vertical)
        
        # --- 上下文区域 ---
        context_frame = QFrame()
        context_frame.setFrameShape(QFrame.Box)
        context_frame.setStyleSheet("QFrame { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; }")
        context_layout = QVBoxLayout(context_frame)
        context_layout.setContentsMargins(10, 10, 10, 10)
        
        context_label = BodyLabel("📖 原文上下文")
        context_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        context_layout.addWidget(context_label)
        
        self.context_display = TextEdit()
        self.context_display.setReadOnly(True)
        self.context_display.setMaximumHeight(120)
        self.context_display.setPlaceholderText("（上下文信息）")
        context_layout.addWidget(self.context_display)
        
        content_splitter.addWidget(context_frame)
        
        # --- 主要内容区域 ---
        main_content_frame = QFrame()
        main_content_layout = QVBoxLayout(main_content_frame)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(15)
        
        # 原文
        source_widget = self._create_text_section("📝 原文", is_editable=False)
        self.source_text_edit = source_widget[1]
        main_content_layout.addWidget(source_widget[0])
        
        # 译文
        translation_widget = self._create_text_section("🌐 译文", is_editable=False)
        self.translation_text_edit = translation_widget[1]
        main_content_layout.addWidget(translation_widget[0])
        
        # 回译
        back_widget = self._create_text_section("🔄 回译", is_editable=False)
        self.back_text_edit = back_widget[1]
        main_content_layout.addWidget(back_widget[0])
        
        # 评分
        score_widget = QWidget()
        score_layout = QHBoxLayout(score_widget)
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_label = BodyLabel("⭐ 质量评分:")
        score_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.score_value_label = BodyLabel("0.0/10")
        self.score_value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        score_layout.addWidget(score_label)
        score_layout.addWidget(self.score_value_label)
        score_layout.addStretch()
        main_content_layout.addWidget(score_widget)
        
        # 用户输入区域（用于自定义翻译）
        custom_widget = self._create_text_section("✏️ 您的翻译（可选）", is_editable=True)
        self.custom_text_edit = custom_widget[1]
        self.custom_text_edit.setPlaceholderText("如果您不满意当前译文，可以在这里输入您希望的翻译...")
        main_content_layout.addWidget(custom_widget[0])
        
        content_splitter.addWidget(main_content_frame)
        content_splitter.setStretchFactor(0, 1)  # 上下文占1份
        content_splitter.setStretchFactor(1, 4)  # 主内容占4份
        
        main_layout.addWidget(content_splitter)
        
        # ========== 底部：操作按钮 ==========
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # 左侧：跳过全部
        self.skip_all_btn = PushButton("跳过全部")
        self.skip_all_btn.setIcon(FIF.CANCEL)
        self.skip_all_btn.clicked.connect(self._on_skip_all)
        button_layout.addWidget(self.skip_all_btn)
        
        button_layout.addStretch()
        
        # 右侧：主要操作按钮
        self.accept_btn = PushButton("接受译文")
        self.accept_btn.setIcon(FIF.ACCEPT)
        self.accept_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(self.accept_btn)
        
        self.reject_btn = PushButton("不接受（重新翻译）")
        self.reject_btn.setIcon(FIF.UPDATE)
        self.reject_btn.clicked.connect(self._on_reject)
        button_layout.addWidget(self.reject_btn)
        
        self.custom_btn = PushButton("使用我的翻译")
        self.custom_btn.setIcon(FIF.EDIT)
        self.custom_btn.clicked.connect(self._on_custom)
        button_layout.addWidget(self.custom_btn)
        
        main_layout.addWidget(button_widget)
        
        # ========== 底部提示 ==========
        tip_label = BodyLabel("💡 提示：接受=使用当前译文 | 不接受=LLM重新翻译 | 使用我的翻译=使用您输入的内容")
        tip_label.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        main_layout.addWidget(tip_label)
        
    def _create_text_section(self, title: str, is_editable: bool = False) -> tuple:
        """创建文本展示/编辑区域"""
        section_frame = QFrame()
        section_frame.setFrameShape(QFrame.Box)
        section_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; }")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(5)
        
        title_label = BodyLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        section_layout.addWidget(title_label)
        
        text_edit = TextEdit()
        text_edit.setReadOnly(not is_editable)
        text_edit.setMaximumHeight(100)
        section_layout.addWidget(text_edit)
        
        return (section_frame, text_edit)
    
    def _show_current_item(self):
        """显示当前审核项"""
        if self.current_item_index >= len(self.review_items):
            # 所有项目审核完成
            self._finish_review()
            return
        
        item = self.review_items[self.current_item_index]
        
        # 更新进度
        self.progress_label.setText(f"当前: {self.current_item_index + 1}/{len(self.review_items)}")
        
        # 更新上下文
        context_parts = []
        if item.get("context_before"):
            context_parts.append(f"【上文】\n{item['context_before']}")
        context_parts.append(f"【当前】\n{item['source_text']}")
        if item.get("context_after"):
            context_parts.append(f"【下文】\n{item['context_after']}")
        self.context_display.setPlainText("\n\n".join(context_parts))
        
        # 更新原文
        self.source_text_edit.setPlainText(item["source_text"])
        
        # 更新译文
        self.translation_text_edit.setPlainText(item["translated_text"])
        
        # 更新回译
        self.back_text_edit.setPlainText(item.get("back_translation", "（无回译）"))
        
        # 更新评分（根据分数显示不同颜色）
        score = item.get("score", 0.0)
        self.score_value_label.setText(f"{score:.1f}/10")
        if score < 5.0:
            color = "#d32f2f"  # 红色
        elif score < 7.0:
            color = "#f57c00"  # 橙色
        else:
            color = "#388e3c"  # 绿色
        self.score_value_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        
        # 清空用户输入
        self.custom_text_edit.clear()
        
    def _on_accept(self):
        """用户选择接受当前译文"""
        item = self.review_items[self.current_item_index]
        self.review_results.append({
            "index": item["index"],
            "action": "accept",
            "translation": item["translated_text"]
        })
        self.info(f"用户接受第{item['index']+1}行译文")
        self._next_item()
    
    def _on_reject(self):
        """用户选择不接受，需要LLM重新翻译"""
        item = self.review_items[self.current_item_index]
        self.review_results.append({
            "index": item["index"],
            "action": "retranslate",
            "translation": None
        })
        self.info(f"用户拒绝第{item['index']+1}行译文，标记为需要重新翻译")
        self._next_item()
    
    def _on_custom(self):
        """用户选择使用自定义翻译"""
        custom_text = self.custom_text_edit.toPlainText().strip()
        
        if not custom_text:
            # 用户没有输入内容
            MessageBox(
                "提示",
                "您还没有输入自定义翻译，请在输入框中填写您希望的翻译内容。",
                self
            ).exec()
            return
        
        item = self.review_items[self.current_item_index]
        self.review_results.append({
            "index": item["index"],
            "action": "custom",
            "translation": custom_text
        })
        self.info(f"用户为第{item['index']+1}行提供了自定义翻译")
        self._next_item()
    
    def _on_skip_all(self):
        """跳过所有剩余审核"""
        msg = MessageBox(
            "确认跳过",
            f"确定要跳过剩余的 {len(self.review_items) - self.current_item_index} 行审核吗？\n"
            f"跳过的行将使用LLM重新翻译。",
            self
        )
        if msg.exec():
            # 将剩余的所有项标记为需要重新翻译
            for i in range(self.current_item_index, len(self.review_items)):
                item = self.review_items[i]
                self.review_results.append({
                    "index": item["index"],
                    "action": "retranslate",
                    "translation": None
                })
            self.info(f"用户跳过了剩余 {len(self.review_items) - self.current_item_index} 行审核")
            self._finish_review()
    
    def _next_item(self):
        """移动到下一项"""
        self.current_item_index += 1
        self._show_current_item()
    
    def _finish_review(self):
        """完成审核"""
        self.info(f"审核完成，共审核 {len(self.review_results)} 行")
        self.reviewFinished.emit(self.review_results)
        self.accept()  # 关闭对话框
    
    def get_review_results(self) -> List[Dict]:
        """获取审核结果"""
        return self.review_results

