# -*- coding: utf-8 -*-
import sys
import os
import re
import json
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, QUrl, QSize, QRect, QPoint
from PyQt5.QtGui import (
    QFont, QDesktopServices, QColor, QPainter, QFontMetrics,
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QCheckBox,
    QDialog, QFrame, QShortcut, QMessageBox, QPlainTextEdit, QComboBox,
    QStyledItemDelegate, QStyle, QTextBrowser, QFileDialog, QMenu,
)

APP_TITLE = "快捷语"
APP_VERSION = "v1.0.1"
AUTHOR = "Gorden"

_DATA_DIR = None

def data_dir():
    global _DATA_DIR
    if _DATA_DIR is None:
        base = os.environ.get("APPDATA") or str(Path.home())
        d = Path(base) / "快捷语"
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        _DATA_DIR = d
    return _DATA_DIR

CONFIG_FILE = data_dir() / "config.json"
VAR_RE = re.compile(r"\{([^{}\n]+)\}")

SAMPLE = """# 通用
[等待]（{车次号}请等待）
[变更站台]（{车次号}你的站台已变更为{数字}月台）

# 警告
[垃圾信息]（{用户名} 请不要发送垃圾信息）
[堵路]（{用户名}请不要堵塞道路）
"""

def load_config():
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}

def save_config(cfg):
    try:
        CONFIG_FILE.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8")
    except Exception:
        pass

def default_templates_dir():
    return data_dir() / "templates"

def get_templates_dir():
    p = load_config().get("templates_dir", "")
    if p:
        path = Path(p)
        if path.exists() and path.is_dir():
            return path
    return default_templates_dir()

def ensure_templates():
    d = get_templates_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
        if not any(d.glob("*.txt")):
            (d / "示例.txt").write_text(SAMPLE, encoding="utf-8")
    except Exception:
        pass

def list_templates():
    d = get_templates_dir()
    if not d.exists():
        return []
    return sorted(d.glob("*.txt"))

def load_from_path(p):
    if not p:
        return []
    try:
        return parse(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return []

def is_valid_category(c):
    if not c:
        return False
    if "=" in c or "#" in c:
        return False
    for ch in "[]（）()":
        if ch in c:
            return False
    return True

_CAT_COLORS = [
    "#4caf7a", "#e08a4a", "#a06cf0", "#4a9ce0",
    "#e05a8a", "#c0b04a", "#5ac0c0", "#c0704a",
]

HELP_HTML = f"""
<html>
<body style="background-color:#1a1a1a; color:#ddd;
             font-family:'Microsoft YaHei'; font-size:12px;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:10px 12px 6px 12px;">

<p style="color:#4caf7a; font-size:14px; font-weight:bold;
          margin:0 0 8px 0;">欢迎使用「快捷语」</p>
<p style="margin:0 0 16px 0; line-height:1.6; color:#aaa;">
你好！这是一款专为高效沟通设计的悬浮小工具，作者：{AUTHOR}。<br>
<span style="color:#888;">当前版本：{APP_VERSION}</span><br>
你的所有数据都安全地保存在本地，不会上传到网络。
</p>

<p style="color:#e08a4a; font-size:13px; font-weight:bold;
          margin:0 0 6px 0;">1. 怎么添加我的常用语？</p>
<p style="margin:0 0 14px 0; line-height:1.7;">
· 点击右下角的 <b>✎</b> 可以直接打开记事本修改。<br>
· 或者点击 <b>＋</b> 在弹出的窗口里直接写，更直观。<br>
· 想要回复更灵活？在内容里加上 <b>{{玩家}}</b>、<b>{{车次}}</b> 这种大括号。<br>
&nbsp;&nbsp;发送时它会自动弹窗让你填，填过一次，下次就自动记住了！
</p>

<p style="color:#e08a4a; font-size:13px; font-weight:bold;
          margin:0 0 6px 0;">2. 格式应该怎么写？</p>
<p style="margin:0 0 4px 0;">
<span style="font-family:Consolas;"># 分类名</span><br>
<span style="font-family:Consolas;">[标题]（你要发送的内容）</span>
</p>
<p style="background-color:#252525; color:#e0e0e0;
          font-family:Consolas; font-size:11px;
          margin:0 0 14px 0; padding:8px; border-radius:4px;">
# 问候<br>
[打招呼]（ {{名字}} ，你好呀！）
</p>

<p style="color:#e08a4a; font-size:13px; font-weight:bold;
          margin:0 0 6px 0;">3. 怎么快速发出去？</p>
<p style="margin:0 0 14px 0; line-height:1.7;">
· 点击列表里的任意一条，它就会自动复制到你的剪贴板。<br>
· 如果勾选了底部的「自动粘贴」：<br>
&nbsp;&nbsp;先在游戏里点一下聊天输入框，再点快捷语，<br>
&nbsp;&nbsp;它会自动帮你按下 Ctrl+V 贴进去，无缝衔接！
</p>

<p style="color:#e08a4a; font-size:13px; font-weight:bold;
          margin:0 0 6px 0;">4. 关于模板文件</p>
<p style="margin:0 0 14px 0; line-height:1.7;">
· 默认的数据不会扔在软件旁边，而是安全地存放在你电脑的 AppData 目录下。<br>
· 如果你想把文件放在 D 盘或 U 盘，点顶部的 <b>⚙</b> 就能自由更换位置。<br>
· 做了好几个不同的 txt 文件？点「模板」下拉框可以随时切换。
</p>

<p style="color:#e08a4a; font-size:13px; font-weight:bold;
          margin:0 0 6px 0;">5. 界面小贴士</p>
<p style="margin:0 0 6px 0; line-height:1.7;">
· 按住顶部标题栏可以随意拖动窗口。<br>
· 按住右下角的 <b>◢</b> 可以调整窗口大小。<br>
· 点 <b>📌</b> 可以锁定窗口置顶，不挡视线。
</p>

</td></tr>
</table>
</body>
</html>
"""

def parse(text):
    out = []
    pattern = re.compile(r"\[([^\]]*)\]\s*[（(](.*?)[）)]", re.DOTALL)
    cat = "未分类"
    blocks = []
    cur_buf = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            c = s.lstrip("#").strip()
            if is_valid_category(c):
                if cur_buf:
                    blocks.append((cat, "\n".join(cur_buf)))
                    cur_buf = []
                cat = c
        else:
            cur_buf.append(line)
    if cur_buf:
        blocks.append((cat, "\n".join(cur_buf)))

    for c, block in blocks:
        for m in pattern.finditer(block):
            title = m.group(1).strip()
            content = m.group(2).strip()
            if content:
                out.append({
                    "title": title or content[:10],
                    "content": content,
                    "category": c,
                })
    return out

def extract_vars(text):
    seen, out = set(), []
    for v in VAR_RE.findall(text):
        v = v.strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out

def fill_vars(text, values):
    return VAR_RE.sub(lambda m: values.get(m.group(1).strip(), m.group(0)), text)

def send_ctrl_v():
    try:
        import ctypes
        u = ctypes.windll.user32
        KEYUP = 0x0002
        u.keybd_event(0x11, 0, 0, 0)
        u.keybd_event(0x56, 0, 0, 0)
        u.keybd_event(0x56, 0, KEYUP, 0)
        u.keybd_event(0x11, 0, KEYUP, 0)
        return True
    except Exception:
        return False

DLG_LABEL_STYLE = "color:#ccc;font-size:11px;background:transparent;"
DLG_INPUT_STYLE = (
    "QLineEdit{background:#333;color:#fff;border:1px solid #555;"
    "border-radius:3px;padding:0 5px;font-size:12px;}"
    "QLineEdit:focus{border:1px solid #2f8f5f;}"
)
DLG_TEXT_STYLE = (
    "QPlainTextEdit{background:#333;color:#fff;border:1px solid #555;"
    "border-radius:3px;padding:4px;font-size:12px;}"
    "QPlainTextEdit:focus{border:1px solid #2f8f5f;}"
)
DLG_CANCEL_STYLE = (
    "QPushButton{background:#3a3a3a;color:#ccc;border:none;"
    "border-radius:3px;font-size:11px;}"
    "QPushButton:hover{background:#4a4a4a;}"
)
DLG_OK_STYLE = (
    "QPushButton{background:#2f8f5f;color:#fff;border:none;"
    "border-radius:3px;font-size:11px;}"
    "QPushButton:hover{background:#3aa86f;}"
)

class DragBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag = None

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPos() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() == Qt.LeftButton:
            self.window().move(e.globalPos() - self._drag)

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(380, 480)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QFrame()
        box.setObjectName("helpbox")
        box.setStyleSheet(
            "#helpbox{background:#1a1a1a;border:1px solid #3a3a3a;"
            "border-radius:6px;}")
        outer.addWidget(box)

        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = DragBar()
        bar.setFixedHeight(28)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 0, 4, 0)
        bl.setSpacing(4)
        tl = QLabel("使用说明")
        tl.setStyleSheet(
            "color:#eee;font-size:12px;font-weight:bold;background:transparent;")
        bl.addWidget(tl)
        sub = QLabel(f"{APP_TITLE} {APP_VERSION} · by {AUTHOR}")
        sub.setStyleSheet(
            "color:#666;font-size:10px;background:transparent;")
        bl.addWidget(sub)
        bl.addStretch(1)
        cb = QPushButton("×")
        cb.setFixedSize(20, 20)
        cb.setStyleSheet(
            "QPushButton{background:transparent;color:#888;border:none;"
            "font-size:14px;}"
            "QPushButton:hover{background:#444;color:#fff;border-radius:3px;}")
        cb.clicked.connect(self.accept)
        bl.addWidget(cb)
        lay.addWidget(bar)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:#333;border:none;")
        lay.addWidget(line)

        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setFrameShape(QFrame.NoFrame)
        tb.setHtml(HELP_HTML)
        tb.setStyleSheet("""
            QTextBrowser{background:#1a1a1a;border:none;color:#ddd;
                padding:0;}
            QScrollBar:vertical{background:transparent;width:8px;margin:0;}
            QScrollBar::handle:vertical{background:#3a3a3a;
                border-radius:4px;min-height:24px;}
            QScrollBar::handle:vertical:hover{background:#4a4a4a;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{
                height:0;background:none;}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{
                background:none;}
        """)
        lay.addWidget(tb, 1)

        bw = QHBoxLayout()
        bw.setContentsMargins(10, 6, 10, 8)
        bw.addStretch(1)
        ok = QPushButton("开始使用")
        ok.setFixedSize(76, 24)
        ok.setStyleSheet(
            "QPushButton{background:#2f8f5f;color:#fff;border:none;"
            "border-radius:3px;font-size:12px;}"
            "QPushButton:hover{background:#3aa86f;}")
        ok.clicked.connect(self.accept)
        bw.addWidget(ok)
        lay.addLayout(bw)

        QShortcut("Esc", self, activated=self.accept)

class FieldDialog(QDialog):
    def __init__(self, content, remember=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.inputs = {}
        remember = remember or {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QFrame()
        box.setObjectName("fieldbox")
        box.setStyleSheet(
            "#fieldbox{background:#252525;border:1px solid #3a3a3a;"
            "border-radius:6px;}")
        outer.addWidget(box)

        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(0)

        bar = QWidget()
        bar.setFixedHeight(22)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(8, 0, 4, 0)
        bl.setSpacing(2)
        tl = QLabel("填写内容")
        tl.setStyleSheet("color:#bbb;font-size:11px;background:transparent;")
        bl.addWidget(tl)
        bl.addStretch(1)
        cb = QPushButton("×")
        cb.setFixedSize(18, 18)
        cb.setStyleSheet(
            "QPushButton{background:transparent;color:#888;border:none;"
            "font-size:13px;}"
            "QPushButton:hover{background:#444;color:#fff;border-radius:3px;}")
        cb.clicked.connect(self.reject)
        bl.addWidget(cb)
        lay.addWidget(bar)

        iw = QWidget()
        il = QVBoxLayout(iw)
        il.setContentsMargins(8, 2, 8, 6)
        il.setSpacing(4)
        for v in extract_vars(content):
            row = QHBoxLayout()
            row.setSpacing(4)
            l = QLabel(v)
            l.setStyleSheet(DLG_LABEL_STYLE)
            l.setMinimumWidth(32)
            l.setMaximumWidth(70)
            le = QLineEdit()
            le.setFixedHeight(22)
            le.setStyleSheet(DLG_INPUT_STYLE)
            le.setText(remember.get(v, ""))
            le.returnPressed.connect(self.accept)
            row.addWidget(l)
            row.addWidget(le, 1)
            il.addLayout(row)
            self.inputs[v] = le
        lay.addWidget(iw)

        brow = QHBoxLayout()
        brow.setContentsMargins(8, 0, 8, 0)
        brow.setSpacing(4)
        brow.addStretch(1)
        cancel = QPushButton("取消")
        cancel.setFixedSize(52, 22)
        cancel.setStyleSheet(DLG_CANCEL_STYLE)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("复制")
        ok.setFixedSize(60, 22)
        ok.setDefault(True)
        ok.setStyleSheet(DLG_OK_STYLE)
        ok.clicked.connect(self.accept)
        brow.addWidget(cancel)
        brow.addWidget(ok)
        lay.addLayout(brow)

        QShortcut("Esc", self, activated=self.reject)

        first = next(iter(self.inputs.values()), None)
        if first:
            first.setFocus()
            first.selectAll()

        self.setFixedWidth(240)
        lay.activate()
        self.adjustSize()

    def values(self):
        return {k: w.text() for k, w in self.inputs.items()}

class AddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QFrame()
        box.setObjectName("addbox")
        box.setStyleSheet(
            "#addbox{background:#252525;border:1px solid #3a3a3a;"
            "border-radius:6px;}")
        outer.addWidget(box)

        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = DragBar()
        bar.setFixedHeight(26)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 0, 4, 0)
        bl.setSpacing(4)
        tl = QLabel("添加快捷语")
        tl.setStyleSheet(
            "color:#eee;font-size:12px;font-weight:bold;background:transparent;")
        bl.addWidget(tl)
        sub = QLabel(f"{APP_TITLE} {APP_VERSION} · by {AUTHOR}")
        sub.setStyleSheet(
            "color:#666;font-size:10px;background:transparent;")
        bl.addWidget(sub)
        bl.addStretch(1)
        cb = QPushButton("×")
        cb.setFixedSize(20, 20)
        cb.setStyleSheet(
            "QPushButton{background:transparent;color:#888;border:none;"
            "font-size:14px;}"
            "QPushButton:hover{background:#444;color:#fff;border-radius:3px;}")
        cb.clicked.connect(self.reject)
        bl.addWidget(cb)
        lay.addWidget(bar)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:#333;border:none;")
        lay.addWidget(line)

        iw = QWidget()
        il = QVBoxLayout(iw)
        il.setContentsMargins(10, 8, 10, 0)
        il.setSpacing(3)

        l1 = QLabel("回复内容")
        l1.setStyleSheet(DLG_LABEL_STYLE)
        il.addWidget(l1)

        self.c = QPlainTextEdit()
        self.c.setFixedHeight(84)
        self.c.setStyleSheet(DLG_TEXT_STYLE)
        self.c.setPlaceholderText("必填，可用 {字段名} 表示自定义内容")
        il.addWidget(self.c)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        col_t = QVBoxLayout()
        col_t.setSpacing(3)
        lt = QLabel("显示标题（可空）")
        lt.setStyleSheet(DLG_LABEL_STYLE)
        col_t.addWidget(lt)
        self.t = QLineEdit()
        self.t.setFixedHeight(22)
        self.t.setStyleSheet(DLG_INPUT_STYLE)
        self.t.setPlaceholderText("自动取开头")
        col_t.addWidget(self.t)
        row2.addLayout(col_t, 1)

        col_c = QVBoxLayout()
        col_c.setSpacing(3)
        lc = QLabel("所属分类（可空）")
        lc.setStyleSheet(DLG_LABEL_STYLE)
        col_c.addWidget(lc)
        self.cat = QLineEdit()
        self.cat.setFixedHeight(22)
        self.cat.setStyleSheet(DLG_INPUT_STYLE)
        self.cat.setPlaceholderText("未分类")
        col_c.addWidget(self.cat)
        row2.addLayout(col_c, 1)

        il.addLayout(row2)
        lay.addWidget(iw)

        brow = QHBoxLayout()
        brow.setContentsMargins(10, 10, 10, 8)
        brow.setSpacing(4)
        brow.addStretch(1)
        cancel = QPushButton("取消")
        cancel.setFixedSize(60, 24)
        cancel.setStyleSheet(DLG_CANCEL_STYLE)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("添加")
        ok.setFixedSize(60, 24)
        ok.setDefault(True)
        ok.setStyleSheet(DLG_OK_STYLE)
        ok.clicked.connect(self.accept)
        brow.addWidget(cancel)
        brow.addWidget(ok)
        lay.addLayout(brow)

        QShortcut("Esc", self, activated=self.reject)

        self.setFixedWidth(300)
        lay.activate()
        self.adjustSize()
        self.c.setFocus()

    def data(self):
        return (self.c.toPlainText().strip(),
                self.t.text().strip(),
                self.cat.text().strip())

class ResizeHandle(QLabel):
    def __init__(self, parent=None):
        super().__init__("◢", parent)
        self.setFixedSize(16, 16)
        self.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setToolTip("拖动调整窗口大小")
        self._hover = False
        self._dragging = False
        self._apply_style()

    def _apply_style(self):
        color = "#ddd" if self._hover else "#666"
        self.setStyleSheet(
            f"QLabel{{color:{color};font-size:13px;"
            "background:transparent;border:none;}}")

    def enterEvent(self, e):
        self._hover = True
        self._apply_style()

    def leaveEvent(self, e):
        self._hover = False
        self._apply_style()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self._start_global = e.globalPos()
            self._start_size = self.window().size()

    def mouseMoveEvent(self, e):
        if self._dragging:
            delta = e.globalPos() - self._start_global
            w = max(self.window().minimumWidth(),
                    self._start_size.width() + delta.x())
            h = max(self.window().minimumHeight(),
                    self._start_size.height() + delta.y())
            self.window().resize(w, h)

    def mouseReleaseEvent(self, e):
        self._dragging = False

class ReplyDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        r = index.data(Qt.UserRole)
        if not r:
            return QSize(0, 60)
        return QSize(0, 44)

    def paint(self, painter, option, index):
        r = index.data(Qt.UserRole)
        if not r:
            super().paint(painter, option, index)
            return

        painter.save()
        rect = option.rect

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, QColor("#2f6f4f"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(rect, QColor("#2e2e2e"))
        else:
            painter.fillRect(rect, QColor("#1a1a1a"))

        bar_color = index.data(Qt.UserRole + 1) or "#555"
        painter.fillRect(
            QRect(rect.left(), rect.top() + 2, 4, rect.height() - 4),
            QColor(bar_color),
        )

        title_font = QFont("Microsoft YaHei", 9)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#eee"))
        title_rect = QRect(rect.left() + 11, rect.top() + 4,
                           rect.width() - 16, 18)
        fm1 = QFontMetrics(title_font)
        title_text = fm1.elidedText(r.get("title", ""), Qt.ElideRight,
                                    title_rect.width())
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title_text)

        prev_font = QFont("Microsoft YaHei", 8)
        painter.setFont(prev_font)
        painter.setPen(QColor("#888"))
        preview = r.get("content", "").replace("\n", " ")
        prev_rect = QRect(rect.left() + 11, rect.top() + 22,
                          rect.width() - 16, 16)
        fm2 = QFontMetrics(prev_font)
        preview_text = fm2.elidedText(preview, Qt.ElideRight, prev_rect.width())
        painter.drawText(prev_rect, Qt.AlignLeft | Qt.AlignVCenter, preview_text)

        painter.setPen(QColor("#2a2a2a"))
        painter.drawLine(rect.left(), rect.bottom(),
                         rect.right(), rect.bottom())
        painter.restore()

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} {APP_VERSION} · by {AUTHOR}")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(240, 360)
        self.resize(290, 440)
        self.replies = []
        self.remember = {}
        self.pinned = True
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._restore_title)
        self._build()

        ensure_templates()
        self._refresh_template_combo()
        self._load_current()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QFrame()
        box.setObjectName("box")
        box.setStyleSheet("#box{background:#222;border-radius:8px;}")
        outer.addWidget(box)

        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = DragBar()
        bar.setFixedHeight(26)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 0, 4, 0)
        bl.setSpacing(3)
        self.title_label = QLabel(f"{APP_TITLE} {APP_VERSION}")
        self.title_label.setStyleSheet(
            "color:#eee;font-size:12px;font-weight:bold;background:transparent;")
        bl.addWidget(self.title_label)

        author_label = QLabel(f"by {AUTHOR}")
        author_label.setStyleSheet(
            "color:#666;font-size:10px;background:transparent;")
        bl.addWidget(author_label)
        bl.addStretch(1)

        def mk_icon_btn(text, tip):
            b = QPushButton(text)
            b.setFixedSize(22, 22)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:#aaa;border:none;"
                "font-size:13px;}"
                "QPushButton:hover{background:#3a3a3a;color:#fff;border-radius:4px;}")
            return b

        help_btn = mk_icon_btn("?", "使用说明")
        help_btn.clicked.connect(self.show_help)
        self.pin_btn = mk_icon_btn("📌", "置顶开关")
        self.pin_btn.clicked.connect(self.toggle_pin)
        min_btn = mk_icon_btn("−", "最小化到任务栏")
        min_btn.clicked.connect(self.showMinimized)
        close_btn = mk_icon_btn("×", "退出")
        close_btn.clicked.connect(self.close)
        bl.addWidget(help_btn)
        bl.addWidget(self.pin_btn)
        bl.addWidget(min_btn)
        bl.addWidget(close_btn)
        lay.addWidget(bar)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:#333;border:none;")
        lay.addWidget(line)

        tpl_wrap = QWidget()
        tw = QHBoxLayout(tpl_wrap)
        tw.setContentsMargins(8, 6, 8, 0)
        tw.setSpacing(4)

        tlbl = QLabel("模板")
        tlbl.setStyleSheet("color:#888;font-size:11px;background:transparent;")
        tw.addWidget(tlbl)

        self.template_combo = QComboBox()
        self.template_combo.setFixedHeight(22)
        self.template_combo.setStyleSheet(
            "QComboBox{background:#1a1a1a;color:#eee;border:1px solid #3a3a3a;"
            "border-radius:4px;padding:0 4px;font-size:11px;}"
            "QComboBox:hover{border:1px solid #555;}"
            "QComboBox::drop-down{border:none;width:14px;}"
            "QComboBox QAbstractItemView{background:#2a2a2a;color:#eee;"
            "border:1px solid #444;selection-background-color:#2f6f4f;}")
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        tw.addWidget(self.template_combo, 1)

        open_tpl_btn = mk_icon_btn("📂", "打开当前模板文件夹")
        open_tpl_btn.clicked.connect(self.open_templates_folder)
        tw.addWidget(open_tpl_btn)

        self.folder_menu_btn = mk_icon_btn("⚙", "模板文件夹设置")
        self.folder_menu_btn.clicked.connect(self.show_folder_menu)
        tw.addWidget(self.folder_menu_btn)

        lay.addWidget(tpl_wrap)

        search_wrap = QWidget()
        sw = QHBoxLayout(search_wrap)
        sw.setContentsMargins(8, 4, 8, 4)
        sw.setSpacing(4)

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedHeight(22)
        self.search.setStyleSheet(
            "QLineEdit{background:#1a1a1a;color:#eee;border:1px solid #3a3a3a;"
            "border-radius:4px;padding:0 6px;font-size:12px;}"
            "QLineEdit:focus{border:1px solid #2f8f5f;}")
        self.search.textChanged.connect(self.refresh)
        sw.addWidget(self.search, 1)

        self.cat_combo = QComboBox()
        self.cat_combo.setFixedHeight(22)
        self.cat_combo.setMinimumWidth(70)
        self.cat_combo.setMaximumWidth(96)
        self.cat_combo.setStyleSheet(
            "QComboBox{background:#1a1a1a;color:#eee;border:1px solid #3a3a3a;"
            "border-radius:4px;padding:0 4px;font-size:11px;}"
            "QComboBox:hover{border:1px solid #555;}"
            "QComboBox::drop-down{border:none;width:14px;}"
            "QComboBox QAbstractItemView{background:#2a2a2a;color:#eee;"
            "border:1px solid #444;selection-background-color:#2f6f4f;}")
        self.cat_combo.currentIndexChanged.connect(self.refresh)
        sw.addWidget(self.cat_combo)
        lay.addWidget(search_wrap)

        list_wrap = QWidget()
        lw = QVBoxLayout(list_wrap)
        lw.setContentsMargins(8, 0, 8, 0)
        lw.setSpacing(0)

        self.list = QListWidget()
        self.list.setMouseTracking(True)
        self.list.setItemDelegate(ReplyDelegate(self.list))
        self.list.setStyleSheet("""
            QListWidget{background:#1a1a1a;border:none;color:#eee;
                        border-radius:4px;}
        """)
        self.list.itemClicked.connect(self.on_click)
        lw.addWidget(self.list)
        lay.addWidget(list_wrap, 1)

        bot_wrap = QWidget()
        bw = QHBoxLayout(bot_wrap)
        bw.setContentsMargins(10, 2, 28, 3)
        bw.setSpacing(3)

        self.autop = QCheckBox("自动粘贴")
        self.autop.setCursor(Qt.PointingHandCursor)
        self.autop.setToolTip(
            "点回复后自动按 Ctrl+V 贴到游戏里\n"
            "（先点一下游戏聊天框，再点回复）")
        self.autop.setStyleSheet(
            "QCheckBox{color:#bbb;font-size:10px;spacing:4px;}"
            "QCheckBox::indicator{width:12px;height:12px;"
            "border:1px solid #555;border-radius:3px;background:#1a1a1a;}"
            "QCheckBox::indicator:hover{border:1px solid #888;}"
            "QCheckBox::indicator:checked{background:#2f8f5f;border:1px solid #2f8f5f;}")
        bw.addWidget(self.autop)
        bw.addStretch(1)

        def mk_action_btn(text, tip, slot):
            b = QPushButton(text)
            b.setFixedSize(26, 22)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:#aaa;border:none;"
                "font-size:13px;}"
                "QPushButton:hover{background:#3a3a3a;color:#fff;border-radius:4px;}")
            b.clicked.connect(slot)
            return b

        reload_btn = mk_action_btn("⟳", "刷新（重新读取当前文件）", self.reload)
        edit_btn = mk_action_btn("✎", "打开当前模板修改", self.open_file)
        add_btn = mk_action_btn("＋", "快捷添加一条", self.quick_add)
        bw.addWidget(reload_btn)
        bw.addWidget(edit_btn)
        bw.addWidget(add_btn)
        lay.addWidget(bot_wrap)

        self.resize_handle = ResizeHandle(self)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "resize_handle"):
            r = self.resize_handle
            r.move(self.width() - r.width() - 2,
                   self.height() - r.height() - 2)
            r.raise_()

    def _refresh_template_combo(self):
        cur_data = self.template_combo.currentData()
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        for f in list_templates():
            self.template_combo.addItem(f.stem, str(f))
        if cur_data:
            idx = self.template_combo.findData(cur_data)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)
        self.template_combo.blockSignals(False)
        self.template_combo.setToolTip(f"当前目录：{get_templates_dir()}")

    def current_template(self):
        return self.template_combo.currentData()

    def on_template_changed(self, _):
        self._load_current()

    def open_templates_folder(self):
        d = get_templates_dir()
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))

    def show_folder_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#2a2a2a;color:#eee;border:1px solid #444;"
            "padding:4px;}"
            "QMenu::item{padding:5px 18px;border-radius:3px;}"
            "QMenu::item:selected{background:#2f6f4f;}"
            "QMenu::separator{height:1px;background:#444;margin:3px 4px;}")
        act_change = menu.addAction("更换文件夹…")
        act_reset = menu.addAction("恢复默认")
        menu.addSeparator()
        act_open = menu.addAction("打开当前文件夹")

        pos = self.folder_menu_btn.mapToGlobal(
            QPoint(0, self.folder_menu_btn.height()))
        act = menu.exec_(pos)
        if act == act_change:
            self.change_templates_folder()
        elif act == act_reset:
            self.reset_templates_folder()
        elif act == act_open:
            self.open_templates_folder()

    def change_templates_folder(self):
        cur = str(get_templates_dir())
        d = QFileDialog.getExistingDirectory(
            self, "选择文件夹", cur, QFileDialog.ShowDirsOnly)
        if not d:
            return
        path = Path(d)
        if path == default_templates_dir():
            self.reset_templates_folder()
            return
        cfg = load_config()
        cfg["templates_dir"] = str(path)
        save_config(cfg)
        ensure_templates()
        self._refresh_template_combo()
        self._load_current()
        self.flash("已更换文件夹")

    def reset_templates_folder(self):
        cfg = load_config()
        if "templates_dir" in cfg:
            del cfg["templates_dir"]
            save_config(cfg)
        ensure_templates()
        self._refresh_template_combo()
        self._load_current()
        self.flash("已恢复默认")

    def show_help(self):
        dlg = HelpDialog(self)
        cg = self.frameGeometry()
        dlg.move(cg.center().x() - dlg.width() // 2,
                 cg.center().y() - dlg.height() // 2)
        dlg.exec_()

    def _load_current(self):
        path = self.current_template()
        self.replies = load_from_path(path)
        self._update_categories()
        self.refresh()

    def reload(self):
        ensure_templates()
        self._refresh_template_combo()
        self._load_current()
        self.flash("已刷新")

    def _update_categories(self):
        cur = self.cat_combo.currentText()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("全部")
        cats = sorted({r["category"] for r in self.replies
                       if r["category"] and r["category"] != "未分类"})
        for c in cats:
            self.cat_combo.addItem(c)
        if any(r["category"] == "未分类" for r in self.replies):
            self.cat_combo.addItem("未分类")
        idx = self.cat_combo.findText(cur)
        self.cat_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.cat_combo.blockSignals(False)

    def refresh(self):
        kw = self.search.text().strip().lower()
        sel = self.cat_combo.currentText()

        cat_order = []
        for r in self.replies:
            c = r["category"]
            if c not in cat_order:
                cat_order.append(c)
        cat_color = {}
        for i, c in enumerate(cat_order):
            cat_color[c] = _CAT_COLORS[i % len(_CAT_COLORS)]

        self.list.clear()
        shown = 0
        for r in self.replies:
            if sel and sel != "全部" and r["category"] != sel:
                continue
            hay = (r["title"] + r["content"] + r["category"]).lower()
            if kw and kw not in hay:
                continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, r)
            item.setData(Qt.UserRole + 1, cat_color.get(r["category"], "#555"))
            item.setToolTip(r["content"])
            self.list.addItem(item)
            shown += 1
        if shown == 0:
            it = QListWidgetItem("暂无内容\n点 ? 看说明 · 点 ✎ 写内容")
            it.setFlags(Qt.NoItemFlags)
            it.setTextAlignment(Qt.AlignCenter)
            self.list.addItem(it)

    def on_click(self, item):
        r = item.data(Qt.UserRole)
        if not r or not r.get("content"):
            return
        content = r["content"]
        if extract_vars(content):
            dlg = FieldDialog(content, self.remember, self)
            dlg.adjustSize()
            cg = self.frameGeometry()
            dlg.move(cg.center().x() - dlg.width() // 2,
                     cg.center().y() - dlg.height() // 2)
            if dlg.exec_() != QDialog.Accepted:
                return
            vals = dlg.values()
            self.remember.update(vals)
            content = fill_vars(content, vals)
        QApplication.clipboard().setText(content)
        self.flash("✅ 已复制")
        if self.autop.isChecked():
            self._autopaste()

    def _autopaste(self):
        self.hide()
        def do():
            if not send_ctrl_v():
                self.flash("自动粘贴失败")
            QTimer.singleShot(180, self._show_back)
        QTimer.singleShot(280, do)

    def _show_back(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def flash(self, text):
        self.title_label.setText(text)
        self._flash_timer.start(1500)

    def _restore_title(self):
        self.title_label.setText(f"{APP_TITLE} {APP_VERSION}")

    def open_file(self):
        path = self.current_template()
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            self.open_templates_folder()

    def _last_category_in_file(self):
        path = self.current_template()
        if not path:
            return ""
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except Exception:
            return ""
        last = ""
        for l in lines:
            s = l.strip()
            if s.startswith("#"):
                c = s.lstrip("#").strip()
                if is_valid_category(c):
                    last = c
        return last

    def quick_add(self):
        path = self.current_template()
        if not path:
            QMessageBox.information(
                self, "提示",
                "还没有文件。\n点 📂 打开文件夹新建一个 .txt，\n"
                "再点 ⟳ 刷新即可。")
            return
        dlg = AddDialog(self)
        cur_cat = self.cat_combo.currentText()
        if cur_cat and cur_cat not in ("全部", "未分类"):
            dlg.cat.setText(cur_cat)
        cg = self.frameGeometry()
        dlg.move(cg.center().x() - dlg.width() // 2,
                 cg.center().y() - dlg.height() // 2)
        if dlg.exec_() != QDialog.Accepted:
            return
        content, title, cat = dlg.data()
        if not content:
            return
        if any(ch in content for ch in "（）()"):
            ret = QMessageBox.question(
                self, "提示",
                "内容里有括号，可能会打断解析。\n是否仍然写入？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret != QMessageBox.Yes:
                return
        title = re.sub(r"[\[\]（）()]", "", title).strip()
        if not title:
            auto = re.sub(r"[\[\]（）()]", "", content[:10]).strip()
            title = auto or "回复"
        cat = re.sub(r"[=#\[\]（）()]", "", cat).strip()
        try:
            with open(path, "a", encoding="utf-8") as f:
                last_cat = self._last_category_in_file()
                if cat and cat != "未分类" and cat != last_cat:
                    f.write(f"\n# {cat}\n")
                f.write(f"[{title}]（{content}）\n")
        except Exception as e:
            QMessageBox.warning(self, "写入失败", str(e))
            return
        self.reload()

    def toggle_pin(self):
        self.pinned = not self.pinned
        flags = self.windowFlags()
        if self.pinned:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.pin_btn.setText("📌" if self.pinned else "📍")

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))
    w = Main()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()