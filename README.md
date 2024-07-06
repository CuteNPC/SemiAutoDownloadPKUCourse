# A Semi-Automatic PKU Course Download Tool

by CuteNPC

### Installation

1. Clone the repository to your local machine:
```
git clone https://github.com/CuteNPC/SemiAutoDownloadPKUCourse.git
```

2. Install `requests` and `tqdm` in your Python environment:
```
pip install requests tqdm
```

3. Install `ffmpeg` and config the `PATH`, Run `ffmpeg -version` to verify the installation.

### Usage

1. Log in to [course.pku.edu.cn](https://course.pku.edu.cn/) using your browser. Open any course replay page, press F12 to open the developer tools, enter:
```
console.log(document.cookie.split('; ').find(row => row.startsWith("_token")).split('=')[1]);
```
in the console and copy the result into a file named `token.txt`.

2. Open course playback page, click `复制下载地址`, and paste the links into `course.txt`, one per line. Multiple lines can be pasted.

3. Change the output in config.json to your desired output folder. If not modified, it will output to the output folder in the current directory by default.

4. Run `main.py` to download the courses.

```
python main.py
```