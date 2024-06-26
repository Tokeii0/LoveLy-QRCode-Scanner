import time
import cv2
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

depro = 'model/detect.prototxt'
decaf = 'model/detect.caffemodel'
srpro = 'model/sr.prototxt'
srcaf = 'model/sr.caffemodel'

def adjust_image(imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0):
    if grayscale:
        imgdata = cv2.cvtColor(imgdata, cv2.COLOR_BGR2GRAY)
    if contrast != 1.0 or brightness != 0:
        imgdata = cv2.convertScaleAbs(imgdata, alpha=contrast, beta=brightness)
    if blur > 0:
        imgdata = cv2.GaussianBlur(imgdata, (blur, blur), 0)
    return imgdata

def decodeQrcode(imgdata, grayscale=False, contrast=1.0, brightness=0, blur=0):
    imgdata = adjust_image(imgdata, grayscale, contrast, brightness, blur)
    detector_wechat = cv2.wechat_qrcode_WeChatQRCode(depro, decaf, srpro, srcaf)
    results, points = detector_wechat.detectAndDecode(imgdata)
    return results, grayscale, contrast, brightness, blur

def brute_force_decode(imgdata, grayscale_options, contrast_options, brightness_options, blur_options):
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for grayscale in grayscale_options:
            for contrast in contrast_options:
                for brightness in brightness_options:
                    for blur in blur_options:
                        futures.append(executor.submit(decodeQrcode, imgdata, grayscale, contrast, brightness, blur))
        
        for future in as_completed(futures):
            results, grayscale, contrast, brightness, blur = future.result()
            if results and results[0]:
                return results[0], grayscale, contrast, brightness, blur  # Return the first successful result
    
    return None, None, None, None, None  # Return None if no successful result is found

if __name__ == '__main__':
    start_time = time.time()  # Start the timer

    img_dir = r'test'
    grayscale_options = [True]
    contrast_options = [1, 2, 3, 4, 5]
    brightness_options = [-50, 0, 50]
    blur_options = [7, 3, 5, 0, 9, 11, 13, 15, 17, 25]

    size_ratios = [0.2, 0.1, 0.3]  # Ratios for original size, 50%, 30%, and 10%

    total_images = 0
    successful_decodes = 0

    # Store images in memory
    images = {}
    for file in os.listdir(img_dir):
        if file.endswith('.png') or file.endswith('.jpg'):
            img_path = os.path.join(img_dir, file)
            imgdata = cv2.imread(img_path)
            images[file] = imgdata

    for file, imgdata in tqdm(images.items(), desc="Processing images"):
        for ratio in tqdm(size_ratios, desc=f"Resizing {file}", leave=False):
            resized_imgdata = cv2.resize(imgdata, (int(imgdata.shape[1] * ratio), int(imgdata.shape[0] * ratio)))
            result, grayscale, contrast, brightness, blur = brute_force_decode(resized_imgdata, grayscale_options, contrast_options, brightness_options, blur_options)
            if result:
                successful_decodes += 1
                #print(f'File: {file}, Size ratio: {ratio}, Decode result: {result}, grayscale: {grayscale}, contrast: {contrast}, brightness: {brightness}, blur: {blur}')
                break
        else:
            print(f'File: {file}, No valid QR code found.')
        total_images += 1

    end_time = time.time()  # End the timer

    if total_images > 0:
        recognition_rate = (successful_decodes / total_images) * 100
        print(f'Total images: {total_images}, Successful decodes: {successful_decodes}, Recognition rate: {recognition_rate:.2f}%')
    
    print(f'Total time taken: {end_time - start_time:.2f} seconds')  # Print the total time taken
