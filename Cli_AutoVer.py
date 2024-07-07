import cv2
import numpy as np
import random
import time

class DecodeThread:
    def __init__(self, imgdata, filename, grayscale_options, contrast_options, brightness_options, blur_options, resize_options, expected_count=10, randomize=False, invert_option=False, threshold=50, show_grayscale=True):
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
        self.invert_option = invert_option
        self.detected_points = []
        self._is_stopped = False
        self.show_grayscale = show_grayscale

    def stop(self):
        self._is_stopped = True

    def adjust_image(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0, binarize=False, invert=False):
        if invert:
            imgdata = cv2.bitwise_not(imgdata)
        if grayscale:
            imgdata = cv2.cvtColor(imgdata, cv2.COLOR_BGR2GRAY)
        if binarize:
            _, imgdata = cv2.threshold(imgdata, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        if contrast != 1.0 or brightness != 0:
            imgdata = cv2.convertScaleAbs(imgdata, alpha=contrast, beta=brightness)
        if blur > 0:
            imgdata = cv2.GaussianBlur(imgdata, (blur, blur), 0)
        return imgdata

    def resize_image(self, imgdata, scale):
        width = int(imgdata.shape[1] * scale)
        height = int(imgdata.shape[0] * scale)
        return cv2.resize(imgdata, (width, height))

    def decodeQrcode(self, imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0, binarize=False, invert=False):
        imgdata = self.adjust_image(imgdata, grayscale, contrast, brightness, blur, binarize, invert)
        detector_wechat = cv2.wechat_qrcode_WeChatQRCode(depro, decaf, srpro, srcaf)
        results, points = detector_wechat.detectAndDecode(imgdata)
        return results, points, grayscale, contrast, brightness, blur, binarize, invert

    def is_duplicate(self, new_points):
        for points in self.detected_points:
            dist = np.linalg.norm(np.array(new_points) - np.array(points))
            if dist < self.threshold:
                return True
        return False

    def brute_force_decode(self):
        total_tasks = len(self.grayscale_options) * len(self.contrast_options) * len(self.brightness_options) * len(self.blur_options) * len(self.resize_options)
        if self.invert_option:
            total_tasks *= 2
        completed_tasks = 0
        detected_results = []

        def get_random_values():
            resize = random.choice(self.resize_options)
            grayscale = random.choice(self.grayscale_options)
            contrast = random.choice(self.contrast_options)
            brightness = random.choice(self.brightness_options)
            blur = random.choice(self.blur_options)
            binarize = random.choice([True, False])
            invert = random.choice([True, False]) if self.invert_option else False
            return resize, grayscale, contrast, brightness, blur, binarize, invert

        while not self._is_stopped and len(self.detected_points) < self.expected_count:
            start_time = time.time()
            if self.randomize:
                resize, grayscale, contrast, brightness, blur, binarize, invert = get_random_values()
                resized_img = self.resize_image(self.imgdata, resize)
                results, points, _, _, _, _, _, _ = self.decodeQrcode(resized_img, grayscale, contrast, brightness, blur, binarize, invert)
                completed_tasks += 1
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
                                formatted_point = [[round(coord[0], 1), round(coord[1], 1)] for coord in scaled_points]
                                elapsed_time = time.time() - start_time
                                print(f" 文件: {self.filename}\n 扫码结果: {result}\n 四角坐标: {formatted_point}\n 亮度: {brightness}, 对比度: {contrast}, 模糊: {blur}\n 缩放比例: {resize}\n 反色: {invert}\n 该轮耗时：{elapsed_time:.2f}秒")
            else:
                for resize in self.resize_options:
                    resized_img = self.resize_image(self.imgdata, resize)
                    for grayscale in self.grayscale_options:
                        for contrast in self.contrast_options:
                            for brightness in self.brightness_options:
                                for blur in self.blur_options:
                                    for binarize in [True, False]:
                                        for invert in ([True, False] if self.invert_option else [False]):
                                            if self._is_stopped or len(self.detected_points) >= self.expected_count:
                                                return
                                            results, points, _, _, _, _, _, _ = self.decodeQrcode(resized_img, grayscale, contrast, brightness, blur, binarize, invert)
                                            completed_tasks += 1
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
                                                            formatted_point = [[round(coord[0], 1), round(coord[1], 1)] for coord in scaled_points]
                                                            elapsed_time = time.time() - start_time
                                                            print(f" 文件: {self.filename}\n 扫码结果: {result}\n 四角坐标: {formatted_point}\n 亮度: {brightness}, 对比度: {contrast}, 模糊: {blur}\n 缩放比例: {resize}\n 反色: {invert}\n 该轮耗时：{elapsed_time:.2f}秒")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="暴力破解二维码解码器")
    parser.add_argument("image", type=str, help="图像文件路径")
    parser.add_argument("-e", "--expected_count", type=int, default=1, help="预期的二维码数量")
    parser.add_argument("-r", "--randomize", action='store_true', help="随机化参数")
    parser.add_argument("-i", "--invert", action='store_true', help="反转颜色")
    parser.add_argument("-g", "--grayscale", action='store_true', help="显示灰度图像")
    args = parser.parse_args()


    depro = 'model/detect.prototxt'
    decaf = 'model/detect.caffemodel'
    srpro = 'model/sr.prototxt'
    srcaf = 'model/sr.caffemodel'

    imgdata = cv2.imread(args.image)
    decoder = DecodeThread(imgdata, args.image, [True], [2, 1, 3], [-75, 75, -50, -25, -10, 0, 25, 50], [-7, -3, 7, 3, -1, 5, 9, 11, 13, 15, 17, 19, 21, 23, 25], [0.2, 0.5, 0.7, 0.9, 1.3, 2.0], expected_count=args.expected_count, randomize=args.randomize, invert_option=args.invert, show_grayscale=args.grayscale)
    decoder.brute_force_decode()