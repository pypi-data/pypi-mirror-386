from ctypes import c_int, sizeof

from PySide2.QtCore import (  # noqa: F401
    qVersion,
    Qt,
    QRect,
    QObject,
    QEvent,
    QSize,
    QByteArray,
    QBuffer,
    QTimer,
    QRectF,
    QThread,
    QSizeF,
    QPointF,
    QPoint,
    QStringListModel,
    QSortFilterProxyModel,
    QItemSelection,
    QModelIndex,
)
from PySide2.QtGui import (  # noqa: F401
    QPixmap,
    QMouseEvent,
    QPalette,
    QCursor,
    QIcon,
    QPainter,
    QStandardItemModel,
    QStandardItem,
    QColor,
    QFont,
    QFontDatabase,
    QRawFont,
    QTransform,
    QImage,
    QIconEngine,
    QResizeEvent,
    QKeySequence,
    QFontMetrics,
    QFontMetricsF,
    QTextLayout,
    QTextOption,
)
from PySide2.QtWidgets import (  # noqa: F401
    QMainWindow,
    QWidget,
    QApplication,
    QDialog,
    QSplashScreen,
    QProgressBar,
    QLabel,
    QToolButton,
    QSlider,
    QAction,
    QSizePolicy,
    QFrame,
    QGraphicsView,
    QGraphicsScene,
    QVBoxLayout,
    QTreeView,
    QDialogButtonBox,
    QAbstractItemView,
    QListView,
    QToolBar,
    QComboBox,
    QLineEdit,
    QShortcut,
    QFileDialog,
    QStatusBar,
    QPushButton,
    QHBoxLayout,
    QMenuBar,
    QMenu,
    QStackedWidget,
    QTextEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractButton,
    QMessageBox,
    QProgressDialog,
    QActionGroup,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QStyle,
    QItemDelegate,
)

# try:
#     # Needed since `QGlyphRun` is not available for PySide2
#     # See spyder-ide/qtawesome#210
#     from qtpy.QtGui import QGlyphRun
# except ImportError:
QGlyphRun = None

INT_SIZE = sizeof(c_int)
INT_MAX = 2**(INT_SIZE*8 - 1) - 1

# from src/gui/painting/qfixed_p.h
QFIXED_MAX = (INT_MAX//256)
