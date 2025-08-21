from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from app import login
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request

class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120))
    xacthuc = db.Column(db.Integer, default=0) # Chưa xác thực = 0; Đã xác thực = 1
    maxacthuc = db.Column(db.Text,default=None)
    solangui = db.Column(db.Integer, default=0) #Số lần gửi mã xác thực, >=10 sẽ khóa tài khoản
    thoihan = db.Column(db.DateTime) #Thời hạn bị khóa tài khoản
    khoatk = db.Column(db.Integer) #Tài khoản bị khóa (=1: bị khóa; =0: không khóa)
    fullname = db.Column(db.String(120))
    img = db.Column(db.String(120), default='/static/hinhanh/face.png')
    imgbase64 = db.Column(db.Text)
    password_hash = db.Column(db.String(128),index=True)
    ndow = db.Column(db.Integer, default = 0)#Số lần xem code
    nview = db.Column(db.Integer, default = 0)#Số lần thưởng khi người khác xem code
    posts = db.relationship('Post', backref='tacgia', lazy='dynamic')
    tailieu = db.relationship('Document', backref='tacgia', lazy='dynamic')
    hlogin = db.relationship('History', backref='accname', lazy='dynamic')
    group = db.relationship('Groupuser', backref='accgr', lazy='dynamic')#Người dùng thuộc nhóm nào
    dethi = db.relationship('Dethiuser', backref='deuser', lazy='dynamic')
    accept = db.relationship('Accept', backref='acceptuser', lazy='dynamic')
    testid = db.relationship('User_tests', backref='usertest', lazy='dynamic') #Người dùng xem test nào
    langdf = db.Column(db.String(10), default="py")
    layout = db.Column(db.Integer, default=6)
    templatecpp = db.Column(db.Text)
    giaovien = db.Column(db.Integer, default=0) #Là giáo viên hay không, 0: không phải giáo viên, 1: là giáo viên
    slhocsinh = db.Column(db.Integer, default=0) #Số lượng học sinh tối đa của giáo viên
    link = db.relationship('Shortlink', backref='usershortlink', lazy='dynamic')
    def __repr__(self):
        return '<User {}>'.format(self.username)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
class Giaovienhs(db.Model): #Cho biết giáo viên nào dạy học sinh nào
    id = db.Column(db.Integer, primary_key=True)
    gv_id = db.Column(db.Integer, db.ForeignKey('user.id')) #ID của giáo viên
    hs_id = db.Column(db.Integer, db.ForeignKey('user.id')) #ID của học sinh
    
class Historym(db.Model): #lịch sử thay đổi điểm của User
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer) #id của User
    dethi = db.Column(db.Integer, default=0) #id của đề thi đóng góp (người khác tải về) hoặc tải điểm
    bainop = db.Column(db.Integer, default=0) #id của Bài tập nộp
    content = db.Column(db.Text) #Nội dung trừ/cộng điểm
    testcase = db.Column(db.Integer, default=0) #Testcase bạn tải về (bị trừ điểm)
    time = db.Column(db.DateTime, default=datetime.now) #Thời gian

class Accept(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    postid = db.Column(db.Integer)
    postidp = db.Column(db.Text)

class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auto = db.Column(db.Boolean,default=False) #Tự động duyệt thành viên
    gname = db.Column(db.String(100),index=True, unique=True)# tên groups
    user  = db.relationship('Groupuser', backref='gracc', lazy='dynamic')
    author= db.Column(db.String(100))

class Groupuser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))#ID groups của người dùng
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))#ID người dùng

#rút gọn link
class Shortlink(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    timeb= db.Column(db.DateTime, index=True, default=datetime.now) #Thời gian tạo link
    key  =  db.Column(db.Text) # Mã rút gọn
    link  =  db.Column(db.Text) # Link gốc
    sl = db.Column(db.Integer, default=0) #Số lượng lượt click
    title = db.Column(db.Text,default="") #Tiêu đề
    timewait = db.Column(db.Integer, default=30) #Thời gian chờ 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stl = db.Column(db.Text,default="") #Trạng thái của link (còn hoạt động hay không)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug=db.Column(db.String(50))
    lop = db.Column(db.String(30))
    tieude = db.Column(db.String(100))
    gioithieu = db.Column(db.Text)
    noidung = db.Column(db.Text)
    congkhai = db.Column(db.Boolean,default=False)
    link = db.Column(db.String(100))
    luotxem = db.Column(db.Integer,default=0)
    diem = db.Column(db.Integer,default=100)
    ngaydang= db.Column(db.DateTime, index=True, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Submitcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timesb= db.Column(db.DateTime, index=True, default=datetime.now)#Thời gian nộp bài
    user = db.Column(db.String(30)) #username người nộp bài
    problem = db.Column(db.Integer,index=True,) #id bài tập
    fulltest = db.Column(db.Integer,default=0)# giá trị 1 là lần nộp đạt điểm tối đa
    result = db.Column(db.Float, default=-1) # kết quả, -1:chưa chấm
    ext = db.Column(db.String(5)) #phần mở rộng của tệp
    code = db.Column(db.Text) #chương trình
    log = db.Column(db.Text) #nội dung file log
    graded = db.Column(db.Integer, default = 0, index=True) #0/1 bài nộp chưa chấm/đã chấm
    numtest = db.Column(db.Integer, default = 0) # Số lượng testcase chấm đúng

class Rank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(30)) #username người nộp bài
    problem = db.Column(db.String(30),index=True,) #id_p bài tập
    numtest = db.Column(db.Integer, default = 0) # Số lượng testcase chấm đúng
    alltest = db.Column(db.Integer, default = 0) # Số lượng testcase tối đa của bài tập
    numsub = db.Column(db.Integer, default = 1) # Số lần nộp bài của user cho 1 bài tập

class Checklog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timesb= db.Column(db.DateTime, default=datetime.now)
    user = db.Column(db.String(30)) #username
    ipx  = db.Column(db.String(30)) #ip của client
    address = db.Column(db.Text) #Chứa router

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timel= db.Column(db.DateTime, index=True, default=datetime.now)
    ip = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class Tags(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    tagname = db.Column(db.String(50)) #vd: ctdl
    tagtitle= db.Column(db.String(200),default="none") #vd: Cấu trúc dữ liệu
    taglink = db.Column(db.String(100),default="none") #Link đến nguồn vd: codeforce.com
    ts   = db.Column(db.DateTime, index=True, default=datetime.now) #Thời gian bắt đầu
    te   = db.Column(db.DateTime, default=datetime.now) #Thời gian kết thúc
    resetrank=db.Column(db.Boolean,default=False) #Chưa dùng đến
    limit      = db.Column(db.Integer, default=0) #Giới hạn đối tượng tham gia Contest, value=id Groups là chỉ cho người trong Groups tham gia
    addview = db.Column(db.Boolean,default=False) # thêm lượt xem cho người dùng: =True => đã thêm 
    post_id = db.relationship('Tag_post', backref='tagpost', lazy='dynamic')#id các bản ghi trong Tag_post
    user = db.Column(db.String(50))#user của user tạo ra tag

class Post(db.Model):
    __tablename__="Post"
    id   = db.Column(db.Integer, primary_key=True)
    id_p = db.Column(db.String(20))
    id_name = db.Column(db.String(100))
    body = db.Column(db.Text)
    created = db.Column(db.DateTime, index=True, default=datetime.now)
    CP = db.Column(db.Integer,default=-1) #0:Puslic; >=1:order;
    numsub = db.Column(db.Integer, default=1)#số lần nộp tối đa được phép
    mucdo = db.Column(db.Integer, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    public = db.Column(db.Boolean,default=True)#Cho phép admin khác dùng
    ac = db.Column(db.Integer, default=0) #Số bài nộp Accept
    allsub = db.Column(db.Integer, default=0) #Tổng số bài nộp
    docx = db.Column(db.LargeBinary)
    sol = db.Column(db.LargeBinary)
    pdf = db.Column(db.LargeBinary)
    source = db.Column(db.Text)
    yt = db.Column(db.Text) #Solution Youtube
    imgbase64 = db.Column(db.Text)

    testcase = db.relationship('Testcase', backref='tc', lazy='dynamic')
    tag_id = db.relationship('Tag_post', backref='posttag', lazy='dynamic')
    de_id = db.relationship('Dethi_post', backref='depost', lazy='dynamic')
    def __repr__(self):
        return '<Post {}>'.format(self.id)
        
class Tag_post(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    id_tag  = db.Column(db.Integer,db.ForeignKey('tags.id'))
    id_post = db.Column(db.Integer,db.ForeignKey('Post.id'))
    no = db.Column(db.Float, default=100, index=True) #số thứ tự của bài tập trong Contest
    point = db.Column(db.Float, default=10) #Điểm của bài tập trong Contest
    maxsub = db.Column(db.Integer, default=1) #Số lần nộp tối đa

class Dethi(db.Model): #Danh sách các đề thi
    id   = db.Column(db.Integer, primary_key=True)
    depdf = db.Column(db.LargeBinary) #Đề thi dạng PDF
    dedocx = db.Column(db.LargeBinary) #Đề thi dạng docx
    docx = db.Column(db.LargeBinary)
    sol = db.Column(db.LargeBinary) #Hướng dẫn chấm *.docx 
    solpdf = db.Column(db.LargeBinary) #Hướng dẫn chấm *.pdf
    notetitle = db.Column(db.String) #Ghi chú, ví dụ của TP Nha Trang, v2 (vòng 2), d2 (ngày 2), Khối 10,...
    kythi = db.Column(db.String) # Kỳ thi nào, ví dụ: Tuyển sinh 10
    makythi = db.Column(db.String) # Mã kỳ thi, ví dụ: ts10
    year  = db.Column(db.Integer) #Năm
    year2 = db.Column(db.String) #Năm học. ví dụ 2023-2024
    tinh = db.Column(db.String) # Đề của tỉnh nào. Ví dụ Khánh Hòa
    username = db.Column(db.String) #người đóng góp. Ví dụ admin
    fname = db.Column(db.String) # Tên file khi người dùng tải file trong quá trình góp đề
    check = db.Column(db.Integer, default=0) # Trạng thái đã duyệt hay chưa. 0: chưa duyệt, 1: đã duyệt và đồng ý, 2: đã duyệt nhưng không đồng ý
    cmt = db.Column(db.String) #Ý kiến của Admin khi duyệt
    ngaygop = db.Column(db.DateTime, index=True, default=datetime.now) #Thời gian góp đề
    ngayduyet = db.Column(db.DateTime) #Thời gian góp đề
    note = db.Column(db.Text) #Ghi chú
    luotxem = db.Column(db.Integer, default=0) #Lượt xem đề
    post_id = db.relationship('Dethi_post', backref='dethipost', lazy='dynamic')
    user_id = db.relationship('Dethiuser', backref='dethiuser', lazy='dynamic')
    
    #Đề thi nào được user nào tải về
class Dethiuser(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    id_dethi  = db.Column(db.Integer,db.ForeignKey('dethi.id'))
    id_user  = db.Column(db.Integer,db.ForeignKey('user.id'))
    ngaytai = db.Column(db.DateTime,default=datetime.now)
    free = db.Column(db.Integer) #1: tải miễn phí, 2: tải bằng điểm

class Dethi_post(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    id_dethi  = db.Column(db.Integer,db.ForeignKey('dethi.id'))
    id_post = db.Column(db.Integer,db.ForeignKey('Post.id'))
    stt = db.Column(db.Integer)
    
class Testcase(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    #inp  = db.Column(db.Text)
    #out  = db.Column(db.Text)
    #fninp  = db.Column(db.Text)
    #fnout  = db.Column(db.Text)
    fnstt  = db.Column(db.Text) #số thứ tự của Test (bắt đầu từ 00)
    post_id = db.Column(db.Integer,  db.ForeignKey('Post.id'), index=True)
    test_id = db.relationship('User_tests', backref='Testcase_test', lazy='dynamic') #Testcase này được người nào xem
    numview = db.Column(db.Integer,default=0)
    
class Captcha(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    noidung = db.Column(db.Text) #Mã Capcha

class User_tests(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, index=True, default=datetime.now) #Thời gian
    userid = db.Column(db.Integer,db.ForeignKey('user.id'))
    testid = db.Column(db.Integer,db.ForeignKey('testcase.id'))

class News(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    title  = db.Column(db.Text)
    content  = db.Column(db.Text)
    user_id  = db.Column(db.Integer)
    times= db.Column(db.DateTime, index=True, default=datetime.now)
    classify = db.Column(db.Text)



class Config(db.Model):
    id  = db.Column(db.Integer, primary_key=True)
    idp = db.Column(db.Integer, index=True) #id bài tập
    prog = db.Column(db.String, default="cpp, pas, py")#ngôn ngữ lập trình cho phép
    juger  = db.Column(db.String, default="c1") #Trình chấm
    tlexe = db.Column(db.Float, default=1) #Thời gian chấm cho *.exe (Pascal, C++)
    tlpy  = db.Column(db.Float, default=2) #Thời gian chấm cho *.py và các ngôn ngữ khác
    memory = db.Column(db.Integer, default=1024) # Bộ nhớ
    exp = db.Column(db.Float, default=0.00001) #Độ chính xác, chỉ dành cho trình chấm c3

class Runexam(db.Model):
    id  = db.Column(db.Integer, primary_key=True)
    idp = db.Column(db.Integer) #id bài tập
    user=db.Column(db.String, default=None) #Tên đăng nhập của user
    inp = db.Column(db.Text)
    ext  = db.Column(db.String(5)) #phần mở rộng của tệp
    code = db.Column(db.Text) #chương trình
    graded = db.Column(db.Integer, default = 0) #0/1 bài nộp chưa chấm/đã chấm

class Imagebase64(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    base64 = db.Column(db.Text) #Chứa mã Base64 của hình ảnh 
    loai  = db.Column(db.Text) #Nhận tiền/ user/ problem/...
    ma = db.Column(db.Text) #Nhận tiền: loại tiền (50,99,149); user: Username; problem: id_p
    ghichu = db.Column(db.Text)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))