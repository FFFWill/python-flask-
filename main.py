from flask import Flask, render_template, send_from_directory,request,redirect,url_for
import os
import socket

app = Flask(__name__, template_folder='.')#对Flask这个类创建实例app,#这里配置一下 template_folder为当前目录，不然可以找不到

def get_ipv6_address():#获取ipv6
    # 获取所有网络接口信息
    interfaces = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6)

    # 过滤出非环回和非链路本地的地址
    for interface in interfaces:
        # interface[4][0] 是 IPv6 地址的字符串形式
        ipv6_address = interface[4][0]
        # 跳过环回地址和链路本地地址
        if not ipv6_address.startswith(('::1', 'fe80:')):
            return ipv6_address

    return None


app.config['UPLOAD_FOLDER'] = 'xqtxt'  # 设置评论文件存储的文件夹

@app.route('/')
def index():
    # 获取videos文件夹中所有的视频文件
    videos = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.endswith('.mp4'):  # .mp4格式
            videos.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    print(len(videos))
    # 将视频列表传递给HTML模板
    return render_template('index.html', videos=videos,ipv6_address=ipv6_address)#将ipv6地址发送到HTML


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # 从GET请求中获取查询参数
    videos_dir = os.path.join(app.root_path, 'videos')
    matched_videos = []

    for filename in os.listdir(videos_dir):
        if filename.endswith('.mp4') and query.lower() in filename.lower():
            matched_videos.append(filename[:-4])  # 移除文件扩展名以获取视频名字

    return render_template('SS.html', videos=matched_videos, ipv6_address=ipv6_address, query=query)


@app.route('/videos/<filename>')
def send_video(filename):
    # 发送视频
    return send_from_directory('videos', filename)

@app.route('/images/<filename>')
def send_image(filename):
    # .jpg
    return send_from_directory('images', filename)


@app.route('/video/<video_name>', methods=['GET', 'POST'])
def video_detail(video_name):
    video_path = os.path.join(app.root_path, 'videos', f'{video_name}.mp4')
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{video_name}.txt')

    txt_content = ''
    comments = []

    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('观众:'):
                    comments.append(line.strip())
                else:
                    txt_content += line

    id_part = extract_id_from_filename(video_name)
    similar_videos_by_name = find_similar_videos_by_name(video_name)
    similar_videos_by_id = find_similar_videos_by_id(id_part)

    if request.method == 'POST':
        comment = request.form.get('comment', '')
        if comment:
            with open(txt_path, 'a', encoding='utf-8') as f:
                f.write(f'观众: {comment}\n')
        return redirect(url_for('video_detail', video_name=video_name))

    if os.path.exists(video_path):
        return render_template('XQ.html', video_name=video_name, txt_content=txt_content,
                               comments=comments,
                               similar_videos_by_name=similar_videos_by_name,
                               similar_videos_by_id=similar_videos_by_id,ipv6_address=ipv6_address)
    else:
        return 'Video not found', 404

def extract_id_from_filename(filename):

    parts = filename.rsplit('_', 1)
    if len(parts) > 1 and parts[-1].isdigit():
        return parts[-1]
    return None

def find_similar_videos_by_name(video_name):
    pass

def find_similar_videos_by_id(id_part):
    if id_part is None:
        return []

    videos_dir = os.path.join(app.root_path, 'videos')
    similar_videos = []
    for filename in os.listdir(videos_dir):
        if filename.endswith('.mp4'):
            basename, _ = os.path.splitext(filename)
            file_id = extract_id_from_filename(basename)
            if file_id == id_part:
                similar_videos.append(basename)
    return similar_videos

###############################################################################################上传视频

UPLOAD_FOLDER_IMAGES = 'images'
UPLOAD_FOLDER_VIDEOS = 'videos'
UPLOAD_FOLDER_TXT = 'xqtxt'

app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['UPLOAD_FOLDER_VIDEOS'] = UPLOAD_FOLDER_VIDEOS
app.config['UPLOAD_FOLDER_TXT'] = UPLOAD_FOLDER_TXT

@app.route('/SC/')
def upload():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files or 'video' not in request.files or 'text' not in request.files or 'filename' not in request.form:
        return 'No file part or filename in the request', 400

    image_file = request.files['image']
    video_file = request.files['video']
    text_file = request.files['text']
    filename = request.form['filename'].strip()

    if not filename:
        return 'Please enter a filename', 400

    if image_file.filename == '' or video_file.filename == '' or text_file.filename == '':
        return 'All files must be selected', 400

    if not (image_file.filename.endswith('.jpg') or image_file.filename.endswith('.jpeg')):
        return 'Image must be in .jpg or .jpeg format', 400

    if not video_file.filename.endswith('.mp4'):
        return 'Video must be in .mp4 format', 400

    if not text_file.filename.endswith('.txt'):
        return 'Text file must be in .txt format', 400

        # Save files with the given filename
    image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], f'{filename}.jpg')
    image_file.save(image_path)

    video_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], f'{filename}.mp4')
    video_file.save(video_path)

    text_path = os.path.join(app.config['UPLOAD_FOLDER_TXT'], f'{filename}.txt')
    text_file.save(text_path)

    # Flash message or redirect after 3 seconds
    return '<p>Upload successful! Redirecting...</p><meta http-equiv="refresh" content="3;url=/" />', 200

###############################################################################################分区

@app.route('/special_movies')
def special_movies():
    # 获取具有"电影_"前缀的视频
    movies = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('电影_') and filename.endswith('.mp4'):
            movies.append(filename[:-4])# 移除文件扩展名以获取视频名字
            #movies.append(filename[3:])
    return render_template('FQ_movies.html', movies=movies,ipv6_address=ipv6_address)

@app.route('/special_TVss')
def special_TVss():
    # 获取具有"影剧_"前缀的视频
    TVss = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('影剧_') and filename.endswith('.mp4'):
            TVss.append(filename[:-4])# 移除文件扩展名以获取视频名字
            #movies.append(filename[3:])
    return render_template('FQ_TVss.html', TVss=TVss,ipv6_address=ipv6_address)

@app.route('/special_animes')
def special_animes():
    # 获取具有"动漫_"前缀的视频
    animes = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('动漫_') and filename.endswith('.mp4'):
            animes.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    return render_template('FQ_animes.html', animes=animes,ipv6_address=ipv6_address)

@app.route('/special_musics')
def special_musics():
    # 获取具有"音乐_"前缀的视频
    musics = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('音乐_') and filename.endswith('.mp4'):
            musics.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    return render_template('FQ_musics.html', musics=musics,ipv6_address=ipv6_address)

@app.route('/special_amuses')
def special_amuses():
    # 获取具有"娱乐_"前缀的视频
    amuses = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('娱乐_') and filename.endswith('.mp4'):
            amuses.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    return render_template('FQ_amuses.html', amuses=amuses,ipv6_address=ipv6_address)

@app.route('/special_techs')
def special_techs():
    # 获取具有"科技_"前缀的视频
    techs = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('科技_') and filename.endswith('.mp4'):
            techs.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    return render_template('FQ_techs.html', techs=techs,ipv6_address=ipv6_address)

@app.route('/special_knows')
def special_knows():
    # 获取具有"知识_"前缀的视频
    knows = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('知识_') and filename.endswith('.mp4'):
            knows.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    return render_template('FQ_knows.html', knows=knows,ipv6_address=ipv6_address)

@app.route('/special_livings')
def special_livings():
    # 获取具有"生活_"前缀的视频
    livings = []
    videos_dir = os.path.join(app.root_path, 'videos')
    for filename in os.listdir(videos_dir):
        if filename.startswith('生活_') and filename.endswith('.mp4'):
            livings.append(filename[:-4])  # 移除文件扩展名以获取视频名字
    return render_template('FQ_livings.html', livings=livings,ipv6_address=ipv6_address)



def extract_key_part(video_name):

    return video_name.replace('电影_', '').replace('影剧_', '').replace('动漫_', '').replace('音乐_', '').replace('娱乐_', '').replace('科技_', '').replace('知识_', '').replace('生活_', '').replace('.mp4', '')



if __name__ == '__main__':
    ipv6_address = get_ipv6_address()
    if ipv6_address:
        app.run(host=ipv6_address, port=80, debug=True, threaded=True)
    else:
        print("No valid IPv6 address found. Falling back to localhost.")
        app.run(host='localhost', port=80, debug=True, threaded=True)
