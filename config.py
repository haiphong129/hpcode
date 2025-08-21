import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    FLASK_DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'luu_hai_phong_akhfua#skdnf@971r78*1tpa'#'luu_hai_phong'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Thư mục chấm bài online
    UPLOAD_FOLDER='app/static/chambai/upload/'
    LOGS_FOLDER ='app/static/chambai/tmp/'

    # Thư mục chứa test các bài được chấm bằng phần mềm Themis
    TESTS_FOLDER='app/static/chambai/test/'#C:/Users/HaiPhong/Desktop/test/'
    DOMAIN = "https://hpcode.edu.vn/"#"http://103.82.20.170/"
    #TESTCASE = "D:/Haiphong129.88/haiphong/hpcode/AllTests/" #C:/Alltest/
    TESTCASE = "app/static/AllT/" #C:/Alltest/
    LOWERCHAR = "qwertyuiopasdfghjklzxcvbnm"
    NUMBER ="1234567890"
    UPPERCHAR = "QWERTYUIOPASDFGHJKLZXCVBNM"
    ALLCHAR = "QWERTYUIOPASDFGHJKLZXCVBNM1234567890qwertyuiopasdfghjklzxcvbnm"

    #SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

    POSTS_PER_PAGE=50

    SHOWTAGS=['laptrinhcb','chuyentincb','chuyentinnc'] #Các mã Contest được phép hiện thị tag trong phần bài tập

    #Theme trong giao diện viewpr
    THEME=["twilight","ambiance","chaos","chrome","clouds","clouds_midnight","cobalt","crimson_editor","dawn","dracula","dreamweaver",
            "eclipse","github","gob","gruvbox","idle_fingers","iplastic","katzenmilch","kr_theme","kuroir","merbivore","merbivore_soft",
            "mono_industrial","monokai","nord_dark","pastel_on_dark","solarized_dark","solarized_light","sqlserver","terminal","textmate",
            "tomorrow","tomorrow_night","tomorrow_night_blue","tomorrow_night_bright","tomorrow_night_eighties","vibrant_ink","xcode"]
    #ký hiệu của ngôn ngữ
    L2L={"c_cpp":"cpp","pascal":"pas","python":"py","scratch":"sb3"}
    L2L_={"cpp":"c_cpp","pas":"pascal","py":"python","sb3":"Scratch"}
    LNAME={"cpp":"C++","pas":"Pascal","py":"Python","sb3":"Scratch"}
    LANG={"c_cpp":"C++","pascal":"Pascal","python":"Python","scratch":"Scratch"}
    LAYOUT={6:"Vertical",10:"Horizontal"}
    ABOUT = "Tác giả: Lưu Hải Phong"
    CV={"Tuyển sinh 10":'ts10',"HSG THCS":'thcs',"HSG Chọn Đội tuyển":'hsga',"HSG THPT":'hsgb',"Olympic 30/4":'o304',"Duyên Hải Bắc Bộ":'dhbb',	"Tin học trẻ":'tht',"Khác...":'khac',"Trại hè":'th'}
    ALLOW_ROUTE=["","themisx","sitemap.xml","homepage","viewcodext","editlink","hplink","updateshortlink","shortlink","viewlink","donate","cp","chinhsach","ads.txt","favicon.ico","downloadfiledoc","listdoc","admin_deldoc","admin_adddoc","admin_delfile","slviewcode","viewcode","viewcodeex","viewsolution","taidethi","gopde","addde","duyetde",
                 "xemde","dethi","downloadde","getpdf","setdef","viewpr","runcodetmp","runcode","submitcode","viewctpr","runexam","solution","getdocx","admin_ql_tintuc","delnew","tintuc","admin_add_group","admin_ql_groups",
                 "admin_del_problem","listproblem","delsub","delsubex","listsubmit","listexam","adminproblem","ranking","resetranking","listuser","changeimg","changepass","info","signup","login","history","vtinhoc",
                 "translate","addviewcontest","contest","viewlog","viewtag","admin_delprtag","admin_del_contest","admin_ql_tags","admin_tagpost","phanloaibt","listcontest","yeucaugr","f5data","addndown","delalltc","upload",
                 "deltest","getAlltests","tct","gettests","uptests","rejuger","hp","video","editv","updateviews","solvideo","getallcode","getuser","static","logout","directlink","xacthuctaikhoan",
                 "loaitkkhoinhom","userdiemcao","xacthuc","khoatk","multiads","giaovien","resetpasshs","delhs","signuphs","addmark","admin_delprtag","admin_tagpost","addgv","delgv","hpx"]
