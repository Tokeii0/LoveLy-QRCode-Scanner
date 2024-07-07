import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QSlider, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
                               QWidget, QTableWidget, QTableWidgetItem, QAbstractItemView)
from PySide6.QtCore import Qt, Slot, QRect, QPoint, QTimer
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QMouseEvent, QIcon
from concurrent.futures import ThreadPoolExecutor
import random

depro = 'model/detect.prototxt'
decaf = 'model/detect.caffemodel'
srpro = 'model/sr.prototxt'
srcaf = 'model/sr.caffemodel'

class ImageDecoder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.imgdata = None
        self.processed_imgdata = None
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.setAcceptDrops(True)
        self.decoded_results = []  # 存储解码结果及其坐标
        self.detected_points = []
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.simulateStep)
        self.tolerance = 30  # 增大容忍度范围，用于去重

    def initUI(self):
        self.setWindowTitle('Lovely QR Code Decoder(手动版本)')
        self.setFixedSize(1200, 700)
        self.setWindowIcon(QIcon('logo.ico'))
        self.originalLabel = ImageLabel()
        self.originalLabel.setFixedSize(400, 400)
        self.originalLabel.setStyleSheet("border: 1px solid black")

        self.processedLabel = ProcessedLabel(self)
        self.processedLabel.setFixedSize(400, 400)
        self.processedLabel.setStyleSheet("border: 1px solid black")

        self.brightnessSlider = QSlider(Qt.Horizontal)
        self.brightnessSlider.setRange(-500, 500) # 增大亮度范围
        self.brightnessSlider.setValue(0)
        self.brightnessSlider.valueChanged.connect(self.updateImage)

        self.contrastSlider = QSlider(Qt.Horizontal)
        self.contrastSlider.setRange(-500, 500) # 增大对比度范围
        self.contrastSlider.setValue(100)
        self.contrastSlider.valueChanged.connect(self.updateImage)

        self.blurSlider = QSlider(Qt.Horizontal)
        self.blurSlider.setRange(0, 50) # 增大模糊范围
        self.blurSlider.setValue(0)
        self.blurSlider.valueChanged.connect(self.updateImage)

        self.resizeSlider = QSlider(Qt.Horizontal)
        self.resizeSlider.setRange(10, 150)
        self.resizeSlider.setValue(100)
        self.resizeSlider.valueChanged.connect(self.updateImage)

        self.erodeSlider = QSlider(Qt.Horizontal)
        self.erodeSlider.setRange(0, 10)
        self.erodeSlider.setValue(0)
        self.erodeSlider.valueChanged.connect(self.updateImage)

        self.brightnessLabel = QLabel('亮度: 0')
        self.contrastLabel = QLabel('对比度: 1.0')
        self.blurLabel = QLabel('模糊: 0')
        self.resizeLabel = QLabel('缩放: 100%')
        self.erodeLabel = QLabel('腐蚀: 0')

        self.openButton = QPushButton('打开图像')
        self.openButton.clicked.connect(self.openImage)

        self.saveButton = QPushButton('保存处理后图像')
        self.saveButton.clicked.connect(self.saveImage)

        self.simulateButton = QPushButton('随机50次')
        self.simulateButton.clicked.connect(self.simulateDrag)

        self.resultTable = QTableWidget()
        self.resultTable.setColumnCount(2)
        self.resultTable.setHorizontalHeaderLabels(['解码结果', '坐标'])
        self.resultTable.cellDoubleClicked.connect(self.highlightQRCode)
        self.resultTable.horizontalHeader().setStretchLastSection(True)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.openButton)
        buttonsLayout.addWidget(self.saveButton)
        buttonsLayout.addWidget(self.simulateButton)

        imagesLayout = QHBoxLayout()
        imagesLayout.addWidget(self.originalLabel)
        imagesLayout.addWidget(self.processedLabel)

        slidersLayout = QVBoxLayout()
        slidersLayout.addWidget(self.brightnessLabel)
        slidersLayout.addWidget(self.brightnessSlider)
        slidersLayout.addWidget(self.contrastLabel)
        slidersLayout.addWidget(self.contrastSlider)
        slidersLayout.addWidget(self.blurLabel)
        slidersLayout.addWidget(self.blurSlider)
        slidersLayout.addWidget(self.resizeLabel)
        slidersLayout.addWidget(self.resizeSlider)
        slidersLayout.addWidget(self.erodeLabel)
        slidersLayout.addWidget(self.erodeSlider)

        leftLayout = QVBoxLayout()
        leftLayout.addLayout(buttonsLayout)
        leftLayout.addLayout(imagesLayout)
        leftLayout.addLayout(slidersLayout)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(leftLayout)
        mainLayout.addWidget(self.resultTable)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

    @Slot()
    def openImage(self):
        fileName, _ = QFileDialog.getOpenFileName(self, '打开图像文件', '', '图像文件 (*.png *.jpg *.bmp)')
        if fileName:
            self.loadImage(fileName)

    def loadImage(self, fileName):
        self.imgdata = cv2.imread(fileName)
        self.processed_imgdata = None
        self.decoded_results.clear()
        self.detected_points.clear()
        self.resultTable.setRowCount(0)
        self.showImage(self.imgdata, self.originalLabel)
        self.updateImage()

    def showImage(self, img, label):
        height, width = label.height(), label.width()
        if len(img.shape) == 3:
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_BGR888)
        else:
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimg).scaled(width, height, Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

    @Slot()
    def updateImage(self):
        if self.imgdata is not None:
            brightness = self.brightnessSlider.value()
            contrast = self.contrastSlider.value() / 100.0
            blur = self.blurSlider.value()
            resize_percent = self.resizeSlider.value()
            erode = self.erodeSlider.value()

            self.brightnessLabel.setText(f'亮度: {brightness}')
            self.contrastLabel.setText(f'对比度: {contrast:.2f}')
            self.blurLabel.setText(f'模糊: {blur}')
            self.resizeLabel.setText(f'缩放: {resize_percent}%')
            self.erodeLabel.setText(f'腐蚀: {erode}')

            resized_imgdata = cv2.resize(self.imgdata, (int(self.imgdata.shape[1] * resize_percent / 100), int(self.imgdata.shape[0] * resize_percent / 100)))
            self.processed_imgdata = self.adjust_image(resized_imgdata, grayscale=True, contrast=contrast, brightness=brightness, blur=blur, erode=erode)
            self.processedLabel.updateImage(self.processed_imgdata)

            result, points = self.decodeQrcode(self.processed_imgdata, grayscale=True, contrast=contrast, brightness=brightness, blur=blur)
            if result:
                for idx, res in enumerate(result):
                    points_resized = points[idx].reshape(4, 2)
                    points_original = [[point[0] / (resize_percent / 100), point[1] / (resize_percent / 100)] for point in points_resized]
                    if not self.is_duplicate(points_original):
                        self.detected_points.append(points_original)
                        self.decoded_results.append((res, points_original))
                        row_position = self.resultTable.rowCount()
                        self.resultTable.insertRow(row_position)
                        self.resultTable.setItem(row_position, 0, QTableWidgetItem(res))
                        self.resultTable.setItem(row_position, 1, QTableWidgetItem(str(points_original)))
                self.markQRCodes()
                self.showImage(self.imgdata.copy(), self.originalLabel)

    def is_duplicate(self, new_points):
        for points in self.detected_points:
            dist = np.linalg.norm(np.array(new_points) - np.array(points))
            if dist < self.tolerance:
                return True
        return False

    def adjust_image(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0, erode=0):
        if grayscale and len(imgdata.shape) == 3:
            imgdata = cv2.cvtColor(imgdata, cv2.COLOR_BGR2GRAY)
        if contrast != 1.0 or brightness != 0:
            imgdata = cv2.convertScaleAbs(imgdata, alpha=contrast, beta=brightness)
        if blur > 0:
            blur = blur if blur % 2 == 1 else blur + 1  # Ensure blur is an odd number
            imgdata = cv2.GaussianBlur(imgdata, (blur, blur), 0)
        if erode > 0:
            kernel = np.ones((erode, erode), np.uint8)
            imgdata = cv2.erode(imgdata, kernel, iterations=1)
        return imgdata

    def decodeQrcode(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0):
        imgdata = self.adjust_image(imgdata, grayscale, contrast, brightness, blur)
        detector_wechat = cv2.wechat_qrcode_WeChatQRCode(depro, decaf, srpro, srcaf)
        results, points = detector_wechat.detectAndDecode(imgdata)
        return results, points

    def markQRCodes(self):
        imgdata_copy = self.imgdata.copy()
        for result, points in self.decoded_results:
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(imgdata_copy, [pts], isClosed=True, color=(0, 0, 255), thickness=7)
        self.showImage(imgdata_copy, self.originalLabel)

    @Slot()
    def highlightQRCode(self, row, column):
        result = self.resultTable.item(row, 0).text()
        points = eval(self.resultTable.item(row, 1).text())
        imgdata_copy = self.imgdata.copy()
        pts = np.array(points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(imgdata_copy, [pts], isClosed=True, color=(0, 0, 255), thickness=7)
        self.showImage(imgdata_copy, self.originalLabel)

    @Slot()
    def saveImage(self):
        if self.processed_imgdata is not None:
            fileName, _ = QFileDialog.getSaveFileName(self, '保存图像文件', '', '图像文件 (*.png *.jpg *.bmp)')
            if fileName:
                cv2.imwrite(fileName, self.processed_imgdata)
                print(f'已保存处理后的图像到 {fileName}')

    @Slot()
    def simulateDrag(self):
        self.simulation_steps = 50
        self.simulation_timer.start(50)

    def simulateStep(self):
        if self.simulation_steps > 0:
            self.brightnessSlider.setValue(random.randint(-100, 100))
            self.contrastSlider.setValue(random.randint(1, 500))
            self.blurSlider.setValue(random.randint(0, 50))
            self.resizeSlider.setValue(random.randint(10, 200))
            self.erodeSlider.setValue(random.randint(0, 10))
            self.updateImage()
            self.simulation_steps -= 1
        else:
            self.simulation_timer.stop()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.loadImage(file_path)

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if hasattr(self, '_pixmap'):
            pixmap = self._pixmap
            width, height = self.width(), self.height()
            img_width, img_height = pixmap.width(), pixmap.height()
            ratio = min(width / img_width, height / img_height)
            new_width, new_height = int(img_width * ratio), int(img_height * ratio)
            self.x_offset = (width - new_width) // 2
            self.y_offset = (height - new_height) // 2
            painter.drawPixmap(self.x_offset, self.y_offset, new_width, new_height, pixmap)
        painter.end()

class ProcessedLabel(ImageLabel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.processed_pixmap = None

    def updateImage(self, imgdata):
        if imgdata is not None:
            self.processed_pixmap = self.convertToPixmap(imgdata)
            self.setPixmap(self.processed_pixmap)

    def convertToPixmap(self, imgdata):
        img = cv2.cvtColor(imgdata, cv2.COLOR_BGR2RGB)
        height, width = img.shape[:2]
        qimg = QImage(img.data, width, height, img.strides[0], QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.parent.drawing = True
            self.parent.start_point = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.parent.drawing:
            self.parent.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.parent.drawing = False
            self.parent.end_point = event.position().toPoint()
            #self.applyMask()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.parent.drawing:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.SolidLine))
            rect = QRect(self.parent.start_point, self.parent.end_point)
            painter.drawRect(rect)
            painter.end()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    decoder = ImageDecoder()
    decoder.show()
    sys.exit(app.exec())
