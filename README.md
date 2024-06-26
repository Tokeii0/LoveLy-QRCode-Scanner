# LoveLy-QRCode-Scanner

### 这是干啥的

对二维码进行爆破解码的脚本，主要用来解码看不清或者微信无法正常扫描的AI生成的二维码

参考了[qrcode-toolkit](https://github.com/antfu/qrcode-toolkit)项目的解码功能

同样调用了[WeChatCV/opencv_3rdparty](https://github.com/WeChatCV/opencv_3rdparty)的解码模型,然后对图片进行，亮度、对比度、模糊度调整，爆破解码

对AI生成的二维码有奇效

### 例子
![2bf23c10108f5b7887128cdca7d6775f](https://github.com/Tokeii0/LoveLy-QRCode-Scanner/assets/111427585/92dc041e-af95-4dcc-bc16-7ef7f1de8a3a)

![1beec49cb901b4d17c607fc5b5536852](https://github.com/Tokeii0/LoveLy-QRCode-Scanner/assets/111427585/2648034d-8806-49a8-89d5-44b33e9ab37c)


### 关于版本

我使用的是

```
python 3.10.11 
opencv-contrib-python                    4.7.0.72
opencv-python                            4.7.0.72
```

### 使用方法

`python gui.py`

或者自己改改代码用main.py

然后拖入文件

### 注意

文件名、目录名中不要有中文


### 参考项目
https://github.com/antfu/qrcode-toolkit

https://github.com/WeChatCV/opencv_3rdparty
