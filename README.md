# LoveLy-QRCode-Scanner

### 这是干啥的

对二维码进行爆破解码的脚本，主要用来解码看不清或者微信无法正常扫描的AI生成的二维码

参考了[qrcode-toolkit](https://github.com/antfu/qrcode-toolkit)项目的解码功能

同样调用了[WeChatCV/opencv_3rdparty](https://github.com/WeChatCV/opencv_3rdparty)的解码模型,然后对图片进行，亮度、对比度、模糊度调整，爆破解码

对AI生成的二维码有奇效

### 例子
![QQ_1720310787282](https://github.com/Tokeii0/LoveLy-QRCode-Scanner/assets/111427585/2704c4dd-e813-4186-9177-f6af81dcb6e1)

![QQ_1720310899349](https://github.com/Tokeii0/LoveLy-QRCode-Scanner/assets/111427585/6470f094-4a1b-4f01-ae03-a076d29f7f38)

![QQ_1720311062281](https://github.com/Tokeii0/LoveLy-QRCode-Scanner/assets/111427585/cbfc3ce4-1715-4740-aec3-abba80327b87)

### 关于版本

我使用的是

```
python 3.10.11 
opencv-contrib-python                    4.7.0.72
opencv-python                            4.7.0.72
```

### 使用方法

```
python Gui_AutoVer.py #自动爆破版本
python Cli_AutoVer.py file [-arg] #命令行版本
python Gui_ManualVer.py #手动调参版本
```

然后拖入文件

### 注意

文件名、目录名中不要有中文


### 参考项目
https://github.com/antfu/qrcode-toolkit

https://github.com/WeChatCV/opencv_3rdparty
