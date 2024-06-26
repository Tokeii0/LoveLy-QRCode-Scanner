import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QTextEdit, QGridLayout, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal

class DecodeThread(QThread):
    progress = Signal(int)
    result = Signal(str)
    croppedImages = Signal(list, list)
    grayscaleImages = Signal(list)
    finished = Signal()
    stopped = Signal()

    def __init__(self, imgdata, filename, grayscale_options, contrast_options, brightness_options, blur_options, threshold=50):
        super().__init__()
        self.imgdata = imgdata
        self.filename = filename
        self.grayscale_options = grayscale_options
        self.contrast_options = contrast_options
        self.brightness_options = brightness_options
        self.blur_options = blur_options
        self.threshold = threshold
        self.detected_points = []
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True

    def adjust_image(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0):
        if grayscale:
            imgdata = cv2.cvtColor(imgdata, cv2.COLOR_BGR2GRAY)
        if contrast != 1.0 or brightness != 0:
            imgdata = cv2.convertScaleAbs(imgdata, alpha=contrast, beta=brightness)
        if blur > 0:
            imgdata = cv2.GaussianBlur(imgdata, (blur, blur), 0)
        return imgdata

    def decodeQrcode(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0):
        imgdata = self.adjust_image(imgdata, grayscale, contrast, brightness, blur)
        detector_wechat = cv2.wechat_qrcode_WeChatQRCode(depro, decaf, srpro, srcaf)
        results, points = detector_wechat.detectAndDecode(imgdata)
        if grayscale:
            # 复制灰度图像用于标注
            grayscale_img_with_boxes = cv2.cvtColor(imgdata, cv2.COLOR_GRAY2BGR)
            for point in points:
                points_array = np.array(point, dtype=np.int32)
                cv2.polylines(grayscale_img_with_boxes, [points_array], True, (0, 0, 255), 5)  # 画红色的框
            self.grayscaleImages.emit([grayscale_img_with_boxes])
        return results, points, grayscale, contrast, brightness, blur

    def is_duplicate(self, new_points):
        for points in self.detected_points:
            dist = np.linalg.norm(np.array(new_points) - np.array(points))
            if dist < self.threshold:
                return True
        return False

    def brute_force_decode(self):
        total_tasks = len(self.grayscale_options) * len(self.contrast_options) * len(self.brightness_options) * len(self.blur_options)
        completed_tasks = 0
        detected_results = []

        for grayscale in self.grayscale_options:
            for contrast in self.contrast_options:
                for brightness in self.brightness_options:
                    for blur in self.blur_options:
                        if self._is_stopped:
                            self.stopped.emit()
                            return
                        results, points, _, _, _, _ = self.decodeQrcode(self.imgdata, grayscale, contrast, brightness, blur)
                        completed_tasks += 1
                        progress = int((completed_tasks / total_tasks) * 100)
                        self.progress.emit(progress)
                        if results:
                            for result, point in zip(results, points):
                                if result and not self.is_duplicate(point):
                                    self.detected_points.append(point)
                                    detected_results.append((result, point))
                                    mask = np.zeros(self.imgdata.shape[:2], dtype=np.uint8)
                                    points = np.array(point, dtype=np.int32)
                                    cv2.fillConvexPoly(mask, points, 1)
                                    self.imgdata = cv2.bitwise_and(self.imgdata, self.imgdata, mask=~mask)
                                    x, y, w, h = cv2.boundingRect(points)
                                    cropped_img = self.imgdata[y:y+h, x:x+w]
                                    self.croppedImages.emit([cropped_img], [point])
                                    formatted_point = [[round(coord[0], 1), round(coord[1], 1)] for coord in point]
                                    self.result.emit(f" 文件: {self.filename}\n 扫码结果: {result}\n 四角坐标: {formatted_point}\n 亮度: {brightness}, 对比度: {contrast}, 模糊: {blur}\n\n")

        self.finished.emit()

    def run(self):
        self.brute_force_decode()

class QRCodeDecoderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('LoveLy QRCode Scanner')
        self.setAcceptDrops(True)

        self.layout = QGridLayout()

        self.uploadLabel = QLabel('拖入载入图片')
        self.uploadLabel.setAlignment(Qt.AlignCenter)
        self.uploadLabel.setFixedSize(300, 300)
        self.layout.addWidget(self.uploadLabel, 0, 0)

        self.processedLabel = QLabel('二维码位置')
        self.processedLabel.setAlignment(Qt.AlignCenter)
        self.processedLabel.setFixedSize(300, 300)
        self.layout.addWidget(self.processedLabel, 0, 1)

        self.grayscaleLabel = QLabel('灰度图')
        self.grayscaleLabel.setAlignment(Qt.AlignCenter)
        self.grayscaleLabel.setFixedSize(300, 300)
        self.layout.addWidget(self.grayscaleLabel, 0, 2)

        self.resultText = QTextEdit()
        self.resultText.setReadOnly(True)
        self.layout.addWidget(self.resultText, 1, 0, 1, 3)

        self.progressBar = QProgressBar(self)
        #self.layout.addWidget(self.progressBar, 2, 1, 1, 2)

        self.stopButton = QPushButton("停止", self)
        self.stopButton.clicked.connect(self.stop_decode)
        hbox = QHBoxLayout()
        hbox.addWidget(self.stopButton)
        hbox.addWidget(self.progressBar)
        self.layout.addLayout(hbox, 2, 0, 1, 3)

        self.comboBox = QComboBox(self)
        self.comboBox.currentIndexChanged.connect(self.on_combobox_changed)
        self.layout.addWidget(self.comboBox, 3, 0, 1, 3)

        self.setLayout(self.layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        #清空上次下拉框结果
        self.resultText.clear()
        self.comboBox.clear()
        self.progressBar.setValue(0)
        self.processedLabel.clear()
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            filePath = urls[0].toLocalFile()
            imgdata = cv2.imread(filePath)
            self.displayImage(imgdata, self.uploadLabel)

            self.decodeThread = DecodeThread(imgdata, filePath, [True], [1, 2, 3, 4, 5,7,8,9], [-50, 0, 50], [7, 3, 5, 0, 9, 11, 13, 15, 17,21, 25])
            self.decodeThread.progress.connect(self.updateProgress)
            self.decodeThread.result.connect(self.appendResult)
            self.decodeThread.croppedImages.connect(self.displayCroppedImages)
            self.decodeThread.grayscaleImages.connect(self.displayGrayscaleImages)
            self.decodeThread.finished.connect(self.on_decode_finished)
            self.decodeThread.stopped.connect(self.on_decode_stopped)
            self.decodeThread.start()

    def stop_decode(self):
        if hasattr(self, 'decodeThread'):
            self.decodeThread.stop()

    def displayImage(self, imgdata, label):
        height, width = imgdata.shape[:2]
        bytesPerLine = 3 * width
        if len(imgdata.shape) == 2:  # Grayscale image
            qImg = QImage(imgdata.data, width, height, width, QImage.Format_Grayscale8)
        else:
            if imgdata.flags['C_CONTIGUOUS']:
                qImg = QImage(imgdata.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            else:
                imgdata = np.ascontiguousarray(imgdata)
                qImg = QImage(imgdata.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio))

    def displayCroppedImages(self, imgdata_list, points_list):
        if not hasattr(self, 'cropped_imgs'):
            self.cropped_imgs = []
            self.points_list = []

        self.cropped_imgs.extend(imgdata_list)
        self.points_list.extend(points_list)

        self.comboBox.clear()
        for i, point in enumerate(self.points_list):
            self.comboBox.addItem(f"QR Code {i+1}: {point.tolist()}")
        self.displayImage(self.cropped_imgs[0], self.processedLabel)

    def displayGrayscaleImages(self, imgdata_list):
        for imgdata in imgdata_list:
            self.displayImage(imgdata, self.grayscaleLabel)

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def appendResult(self, result):
        existing_text = self.resultText.toPlainText()
        if result not in existing_text:
            self.resultText.append(result)

    def on_combobox_changed(self, index):
        if hasattr(self, 'cropped_imgs') and index < len(self.cropped_imgs):
            self.displayImage(self.cropped_imgs[index], self.processedLabel)

    def on_decode_finished(self):
        self.mark_detected_areas()

    def on_decode_stopped(self):
        self.mark_detected_areas()

    def mark_detected_areas(self):
        if hasattr(self, 'decodeThread'):
            imgdata = cv2.cvtColor(self.decodeThread.imgdata, cv2.COLOR_BGR2GRAY)
            imgdata_with_boxes = cv2.cvtColor(imgdata, cv2.COLOR_GRAY2BGR)
            for point in self.decodeThread.detected_points:
                points_array = np.array(point, dtype=np.int32)
                cv2.polylines(imgdata_with_boxes, [points_array], True, (0, 0, 255), 2)  # 画红色的框
            self.displayImage(imgdata_with_boxes, self.grayscaleLabel)

if __name__ == '__main__':
    depro = 'model/detect.prototxt'
    decaf = 'model/detect.caffemodel'
    srpro = 'model/sr.prototxt'
    srcaf = 'model/sr.caffemodel'

    app = QApplication(sys.argv)
    ex = QRCodeDecoderApp()
    ex.show()
    sys.exit(app.exec())
