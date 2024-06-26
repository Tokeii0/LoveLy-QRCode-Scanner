import sys
import cv2
import numpy as np
import random
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QTextEdit, QGridLayout, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout, QSpinBox, QCheckBox
from PySide6.QtGui import QPixmap, QImage, QIcon
from PySide6.QtCore import Qt, QThread, Signal

class DecodeThread(QThread):
    progress = Signal(int)
    result = Signal(str)
    croppedImages = Signal(list, list)
    grayscaleImages = Signal(list)
    finished = Signal()
    stopped = Signal()

    def __init__(self, imgdata, filename, grayscale_options, contrast_options, brightness_options, blur_options, resize_options, expected_count=10, randomize=False, threshold=50):
        super().__init__()
        self.imgdata = imgdata
        self.filename = filename
        self.grayscale_options = grayscale_options
        self.contrast_options = contrast_options
        self.brightness_options = brightness_options
        self.blur_options = blur_options
        self.resize_options = resize_options
        self.threshold = threshold
        self.expected_count = expected_count
        self.randomize = randomize
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

    def resize_image(self, imgdata, scale):
        width = int(imgdata.shape[1] * scale)
        height = int(imgdata.shape[0] * scale)
        return cv2.resize(imgdata, (width, height))

    def decodeQrcode(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0):
        imgdata = self.adjust_image(imgdata, grayscale, contrast, brightness, blur)
        detector_wechat = cv2.wechat_qrcode_WeChatQRCode(depro, decaf, srpro, srcaf)
        results, points = detector_wechat.detectAndDecode(imgdata)
        if grayscale:
            grayscale_img_with_boxes = cv2.cvtColor(imgdata, cv2.COLOR_GRAY2BGR)
            for point in points:
                points_array = np.array(point, dtype=np.int32)
                cv2.polylines(grayscale_img_with_boxes, [points_array], True, (0, 0, 255), 5)
            self.grayscaleImages.emit([grayscale_img_with_boxes])
        return results, points, grayscale, contrast, brightness, blur

    def is_duplicate(self, new_points):
        for points in self.detected_points:
            dist = np.linalg.norm(np.array(new_points) - np.array(points))
            if dist < self.threshold:
                return True
        return False

    def brute_force_decode(self):
        total_tasks = len(self.grayscale_options) * len(self.contrast_options) * len(self.brightness_options) * len(self.blur_options) * len(self.resize_options)
        completed_tasks = 0
        detected_results = []

        def get_random_values():
            resize = random.choice(self.resize_options)
            grayscale = random.choice(self.grayscale_options)
            contrast = random.choice(self.contrast_options)
            brightness = random.choice(self.brightness_options)
            blur = random.choice(self.blur_options)
            return resize, grayscale, contrast, brightness, blur

        while not self._is_stopped and len(self.detected_points) < self.expected_count:
            if self.randomize:
                resize, grayscale, contrast, brightness, blur = get_random_values()
                resized_img = self.resize_image(self.imgdata, resize)
                results, points, _, _, _, _ = self.decodeQrcode(resized_img, grayscale, contrast, brightness, blur)
                completed_tasks += 1
                progress = int((completed_tasks / total_tasks) * 100)
                self.progress.emit(progress)
                if results:
                    for result, point in zip(results, points):
                        if result:
                            scaled_points = [[coord[0] / resize, coord[1] / resize] for coord in point]
                            if not self.is_duplicate(scaled_points):
                                self.detected_points.append(scaled_points)
                                detected_results.append((result, scaled_points))
                                mask = np.zeros(resized_img.shape[:2], dtype=np.uint8)
                                points = np.array(point, dtype=np.int32)
                                cv2.fillConvexPoly(mask, points, 1)
                                resized_img = cv2.bitwise_and(resized_img, resized_img, mask=~mask)
                                x, y, w, h = cv2.boundingRect(points)
                                cropped_img = resized_img[y:y+h, x:x+w]
                                self.croppedImages.emit([cropped_img], [scaled_points])
                                formatted_point = [[round(coord[0], 1), round(coord[1], 1)] for coord in scaled_points]
                                self.result.emit(f" 文件: {self.filename}\n 扫码结果: {result}\n 四角坐标: {formatted_point}\n 亮度: {brightness}, 对比度: {contrast}, 模糊: {blur}\n 缩放比例: {resize}\n")
            else:
                for resize in self.resize_options:
                    resized_img = self.resize_image(self.imgdata, resize)
                    for grayscale in self.grayscale_options:
                        for contrast in self.contrast_options:
                            for brightness in self.brightness_options:
                                for blur in self.blur_options:
                                    if self._is_stopped or len(self.detected_points) >= self.expected_count:
                                        self.stopped.emit()
                                        return
                                    results, points, _, _, _, _ = self.decodeQrcode(resized_img, grayscale, contrast, brightness, blur)
                                    completed_tasks += 1
                                    progress = int((completed_tasks / total_tasks) * 100)
                                    self.progress.emit(progress)
                                    if results:
                                        for result, point in zip(results, points):
                                            if result:
                                                scaled_points = [[coord[0] / resize, coord[1] / resize] for coord in point]
                                                if not self.is_duplicate(scaled_points):
                                                    self.detected_points.append(scaled_points)
                                                    detected_results.append((result, scaled_points))
                                                    mask = np.zeros(resized_img.shape[:2], dtype=np.uint8)
                                                    points = np.array(point, dtype=np.int32)
                                                    cv2.fillConvexPoly(mask, points, 1)
                                                    resized_img = cv2.bitwise_and(resized_img, resized_img, mask=~mask)
                                                    x, y, w, h = cv2.boundingRect(points)
                                                    cropped_img = resized_img[y:y+h, x:x+w]
                                                    self.croppedImages.emit([cropped_img], [scaled_points])
                                                    formatted_point = [[round(coord[0], 1), round(coord[1], 1)] for coord in scaled_points]
                                                    self.result.emit(f" 文件: {self.filename}\n 扫码结果: {result}\n 四角坐标: {formatted_point}\n 亮度: {brightness}, 对比度: {contrast}, 模糊: {blur}\n 缩放比例: {resize}\n")

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
        self.setFixedSize(940, 540)
        self.layout = QGridLayout()
        self.setWindowIcon(QIcon('logo.ico'))

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
        self.stopButton = QPushButton("停止", self)
        self.stopButton.clicked.connect(self.stop_decode)
        hbox = QHBoxLayout()
        hbox.addWidget(self.stopButton)
        hbox.addWidget(self.progressBar)
        self.layout.addLayout(hbox, 2, 0, 1, 3)

        self.comboBox = QComboBox(self)
        self.comboBox.currentIndexChanged.connect(self.on_combobox_changed)
        self.layout.addWidget(self.comboBox, 3, 0, 1, 3)

        self.expectedCountLabel = QLabel('预计二维码个数:')
        self.expectedCountInput = QSpinBox()
        self.expectedCountInput.setRange(1, 100)
        self.expectedCountInput.setValue(1)
        hbox_count = QHBoxLayout()
        hbox_count.addWidget(self.expectedCountLabel)
        hbox_count.addWidget(self.expectedCountInput)
        self.layout.addLayout(hbox_count, 4, 0, 1, 3)

        self.randomCheckBox = QCheckBox("随机选择参数", self)
        self.layout.addWidget(self.randomCheckBox, 5, 0, 1, 3)
        

        self.setLayout(self.layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.resultText.clear()
        self.comboBox.clear()
        self.progressBar.setValue(0)
        self.uploadLabel.clear()
        self.processedLabel.clear()
        self.grayscaleLabel.clear()

        if hasattr(self, 'decodeThread'):
            self.decodeThread.terminate()
        
        if hasattr(self, 'cropped_imgs'):
            del self.cropped_imgs
            del self.points_list

        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            filePath = urls[0].toLocalFile()
            try:
                imgdata = cv2.imread(filePath)
                self.displayImage(imgdata, self.uploadLabel)

                expected_count = self.expectedCountInput.value()
                randomize = self.randomCheckBox.isChecked()
                self.decodeThread = DecodeThread(imgdata, filePath, [True, False], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [-75, -50, -25, 0, 25, 50, 75], [7, 3, 5, 0, 9, 11, 13, 15, 17, 21, 25, 27, 29, 31, 33, 35], [0.2, 0.5, 0.7, 1.3, 2.0], expected_count=expected_count, randomize=randomize)
                self.decodeThread.progress.connect(self.updateProgress)
                self.decodeThread.result.connect(self.appendResult)
                self.decodeThread.croppedImages.connect(self.displayCroppedImages)
                self.decodeThread.grayscaleImages.connect(self.displayGrayscaleImages)
                self.decodeThread.finished.connect(self.on_decode_finished)
                self.decodeThread.stopped.connect(self.on_decode_stopped)
                self.decodeThread.start()
            except Exception as e:
                #对话框，请使用英文路径
                self.resultText.append(f"Error: {e}")


    def stop_decode(self):
        if hasattr(self, 'decodeThread'):
            self.decodeThread.stop()

    def displayImage(self, imgdata, label):
        height, width = imgdata.shape[:2]
        bytesPerLine = 3 * width
        if len(imgdata.shape) == 2:
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
            self.comboBox.addItem(f"QR Code {i+1}: {point}")
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
            imgdata = self.decodeThread.imgdata
            imgdata_with_boxes = cv2.cvtColor(imgdata, cv2.COLOR_BGR2GRAY)
            imgdata_with_boxes = cv2.cvtColor(imgdata_with_boxes, cv2.COLOR_GRAY2BGR)
            for point in self.decodeThread.detected_points:
                points_array = np.array(point, dtype=np.int32)
                cv2.polylines(imgdata_with_boxes, [points_array], True, (0, 0, 255), 5)
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
