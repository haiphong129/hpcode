from app import app
import os, re
from flask_login import current_user
from app.models import *
import time
from datetime import datetime, timedelta
from shutil import copyfile
import shutil, time, string
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup as bs # importing BeautifulSoup

from zipfile import ZipFile, ZIP_DEFLATED
import markdown, pathlib
from pytube import YouTube, Playlist
from pytube.cli import on_progress
from sqlalchemy import func
from random import choice
import random
import pypandoc

#from PyPDF4 import PdfFileWriter, PdfFileReader
from pypdf import PdfReader, PdfWriter

from mailjet_rest import Client
random.seed(100)
from captcha.image import ImageCaptcha
def fhp_permit(group):#Kiểm tra $group có thộc user không?
	if current_user.is_anonymous: return 0
	for gr in group:
		groupid=Groups.query.filter_by(gname=gr).first()
		if groupid is None: continue
		check=current_user.group.filter_by(group_id=groupid.id).first()
		if check is not None: return 1
	return 0
ALLOWED_EXTENSIONS = set(['txt', 'pas', 'cpp', 'jpg', 'jpeg', 'png', 'docx', 'zip'])
#Kiểm tra user thuộc Groups hay không
def checkUserGroup(userid,gname):
	gr = Groups.query.filter_by(gname=gname).first()
	if gr is None: return 0
	return 1 if Groupuser.query.filter(Groupuser.group_id==gr.id,Groupuser.user_id==userid).first() is not None else 0
def haveads(): #kiểm tra user thuộc nhóm không quảng cáo (1: có quảng cáo)
	if current_user.is_anonymous: return 1
	if checkUserGroup(current_user.id,"noads"): return 0
	return 1
def relpaceall(fn,namecontest,sbid): #Xóa toàn bộ đường dẫn trong file log khi chấm bài bằng Themis
	lista = ["hpelearning","Themis","app","static","CodeBlocks","MinGW","ProgramData","C:","D:","ThemisWorkSpace","\\","judle","bin","WorkSpace","WaitRoom"]
	fnx = "app/static/themis/oj/logs/alllog.txt"
	while not os.path.isfile(fn):
		time.sleep(1)
		listfn = [fname for fname in os.listdir("app/static/themis/oj")]
		f = open(fnx,"w",encoding="utf-8")
		if len(listfn)==1: 
			f.write("<h5 class='text-success text-center'>Đang chấm bài...</h5>")
		else: f.write("<h5 class='text-danger text-center'>Đang chấm "+str(len(listfn))+" bài</h5>")
		f.close()
		if os.path.isfile(fn):
			fx = open(fn,"r",encoding="utf-8")
			data = fx.read()
			fx.close()
			for s in lista: data = data.replace(s,"")
			fx = open(fn,"w",encoding="utf-8")
			fx.write(data)
			fx.close()
			fnc = os.path.basename(fn)
			fnc = fn.replace(fnc,"")+namecontest+"/"+fnc
			fxc = open(fnc,"w",encoding="utf-8")
			fxc.write(data)
			fxc.close()
			sb = Submitcode.query.filter_by(id=sbid).first()
			if sb is not None:
				sb.log = data
				db.session.commit()

			return


def put_watermark(input_pdf, output_pdf, watermark): 
    watermark_instance = PdfReader(watermark)
    watermark_page = watermark_instance.get_page(0)
    pdf_reader = PdfReader(input_pdf) 
    pdf_writer = PdfWriter() 
    for page in range(pdf_reader.get_num_pages()):   
        page = pdf_reader.get_page(page) 
        page.merge_page(watermark_page,over=False)
        pdf_writer.add_page(page) 
    with open(output_pdf, 'wb') as out:   
        pdf_writer.write(out)

#Thêm user vào Groups xác định. ví dụ thêm User admin vào Groups ts10
def add_user_into_one_groups(username,gname):
	user = User.query.filter_by(username=username).first()
	if user is None: return
	if checkUserGroup(user.id,gname)==1: return #User đã có
	gr=Groups.query.filter_by(gname=gname).first()
	if gr is None: return # Group không tồn tại
	gnew=Groupuser(user_id=user.id,group_id=gr.id)
	db.session.add(gnew)
	return

#Thêm user vào Groups Sau khi user ủng hộ Website
def add_user_into_groups(username):
	user = User.query.filter_by(username=username).first()
	if user is None: return
	lg = [] #danh sách Groups mà User được thêm vào
	if checkUserGroup(user.id,'g10d2s')==1: lg=['hpltcb','hpctcb']
	if checkUserGroup(user.id,'g1y10s')==1: lg=['hpltcb','hpctcb','ts10']
	if checkUserGroup(user.id,'g1y10ks1')==1: lg=['hpltcb','hpctcb','ts10','hsgthcs']
	if checkUserGroup(user.id,'g1y10ks2')==1:  lg = ['hpltcb','hpctcb','hpctnc','ts10','hsgthcs','hsgthpt','hsgcdt']
	#for x in ['hpts10','hphsgthcs','hphsgthpt','hpcdt']:lg.append(x)
	for gname in lg:
		gr=Groups.query.filter_by(gname=gname).first()
		if checkUserGroup(user.id,gname)==0:
			gnew=Groupuser(user_id=user.id,group_id=gr.id)
			db.session.add(gnew)
	db.session.commit()
	return 
#Xóa User trong Groups
def delete_user_into_groups(username):
	user = User.query.filter_by(username=username).first()
	if user is None: return
	lg = [] #danh sách Groups mà User bị xóa
	if checkUserGroup(user.id,'g10d2s')==1: lg=['hpltcb','hpctcb']
	if checkUserGroup(user.id,'g1y10s')==1: lg=['hpltcb','hpctcb']
	if checkUserGroup(user.id,'g1y10ks1')==1: lg=['hpltcb','hpctcb']
	if checkUserGroup(user.id,'g1y10ks2')==1:  lg = ['hpltcb','hpctcb','hpctnc']
	for x in ['ts10','hsgthcs','hsgthpt','hsgcdt']:lg.append(x)
	for gname in lg:
		gr=Groups.query.filter_by(gname=gname).first()
		check=Groupuser.query.filter(Groupuser.user_id==user.id,Groupuser.group_id==gr.id).first()
		if check is not None: db.session.delete(check)
	db.session.commit()
	return 
def solannpbaiconlai(): #Tính số lần nộp bài còn lại của user cho mỗi bài
	if current_user.is_anonymous: return 0
	ans = 0
	if fhp_permit(['admin'])==1: ans= max(ans,100)
	sldanop = Submitcode.query.filter(Submitcode.user==current_user.username,Submitcode.timesb >= datetime(2024,9,2,0,0,0,0)).count()
	if current_user.giaovien ==1: ans = max(10000 - sldanop,ans)
	if Giaovienhs.query.filter_by(hs_id=current_user.id).first() is not None: 
		ans = max(2000 - sldanop,ans)
		gv = User.query.filter_by(username="giaovien30").first()
		if Giaovienhs.query.filter_by(gv_id=gv.id,hs_id=current_user.id).first() is not None:
			ans = max(300 - sldanop,0)
	return ans
#Lấy đường dẫn đến tên thư mục chứa test
def gettestfilename(post,fnstt):
	prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else "0-9"
	return app.config['TESTCASE']+prefix+"/"+post.id_p#+"/"+fnstt+"/"+post.id_p
def get1test(fntest,stt): #Trả về testcase có số thứ tự stt
	inp,out="",""
	with ZipFile(fntest+".zip", 'r') as zip:
		for fn in zip.namelist():
			if stt.lower() in fn.lower():
				if ".inp" in fn.lower(): inp=zip.read(fn)
				if ".out" in fn.lower(): out=zip.read(fn)
				if inp!="" and out!="": return inp.decode(),out.decode()
	return inp.decode(),out.decode()
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def uploadfiledoc(files,lop,slug):
	root="app/static/document/"
	if not os.path.isdir(root+lop): os.mkdir(root+lop)
	root=root+lop+'/'
	if not os.path.isdir(root+slug): os.mkdir(root+slug)
	root=root+slug+'/'
	if not os.path.isdir(root+'image'): os.mkdir(root+'image')
	for file in files:
		filename = secure_filename(file.filename)
		if filename=="": continue
		if os.path.splitext(filename)[1].lower() in ['.jpg','.png']:
			file.save(os.path.join(root,'image',filename))
		else:
			file.save(os.path.join(root,filename))
	return
def createcapcha():
	image = ImageCaptcha(width = 280, height = 90)
	captcha_text = randomtext(6,string.ascii_lowercase)
	image.character_rotate = (-5, 5)
	image.character_warp_dx = (0.9,1)
	image.character_warp_dy = (0.9,1)
	image.character_offset_dx =  (1,1)
	image.character_offset_dy =  (1,1)
	image.word_space_probability = 1
	image.generate(captcha_text)
	captcha = Captcha(noidung=captcha_text)
	db.session.add(captcha)
	db.session.commit()
	idcaptcha = Captcha.query.filter_by(noidung=captcha_text).first().id
	# write the image on the given file and save it
	fn="app/static/hpcaptchar/"+str(idcaptcha)+".png"
	image.write(captcha_text, fn)
	return idcaptcha
def sent_email_xacthuc(user):
	api_key = "3bb3a0a07fb3f7d06b9bc4b869968e3a"
	api_secret = "997d176e5ce3f5584b4daf0f1eea84f6"
	mailjet = Client(auth=(api_key, api_secret), version='v3.1')
	data = {
  		'Messages': [
						{
						"From": {
								"Email": "haiphong129.88@gmail.com",
								"Name": "admin - hpcode"
						},
						"To": [
								{
										"Email": user.email,
										"Name": user.username+" "+user.fullname
								}
						],
						"Subject": "Xác thực tài khoản",
						"TextPart": "Chào mừng bạn đến với hpcode!",
						"HTMLPart": "<h3>Chuỗi xác thực của bạn: "+user.maxacthuc+"</h3>"
						}
					]
			}
	return mailjet.send.create(data=data)

def get_all_file_in_doc(doc):#lấy tất cả các file trong một tài liệu
	fileall=[]
	if doc is not None:
		root=os.path.join("app/static/document",doc.lop,doc.slug)
		for fn in os.listdir(root):
			if os.path.isfile(os.path.join(root,fn)): fileall.append(fn)

		root=os.path.join(root,"image")
		for fn in os.listdir(root):
			if os.path.isfile(os.path.join(root,fn)): 
				fileall.append(fn)
				copyfile(os.path.join(root,fn),os.path.join("app/static/download",doc.slug+"_"+fn))
	return fileall
def check_VN(s):
	tmp="àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễòóọỏõôồốộổỗơờớợởỡìíịỉĩùúụủũưừứựỳýỵỷỹđ"
	for x in tmp:
		if x in s: return 1
	return 0
def no_accent_vietnamese(s):
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[đ]', 'd', s)
    while "  " in s: s=s.replace("  "," ")
    if(s[0]==" "): s=s[1:]
    if(s[-1]==" "): s=s[:-1]
    return s.replace(" ","-").lower()
def get_all_post_in_tag(cname):
	tag = Tags.query.filter_by(tagname = cname).first()
	if tag is None: return []
	ans = [x.id_post for x in tag.post_id.all()]
	return ans
def get_all_user_in_tag(cname): 
	tag = Tags.query.filter_by(tagname = cname).first()
	if tag is None: return []
	gr = Groups.query.filter_by(id=tag.limit).first()
	ans=[]
	for x in gr.user.all():
		user = User.query.filter_by(id=x.user_id).first()
		if user is None: continue
		ans.append(user.username)
	return ans
#Cập nhận thống kê khi có bài nộp
def updatestatic(sb):
	fn = "app/static/data/thongke.txt"
	f = open(fn,"r")
	tdata= eval(f.read())
	tdata['AC']+=sb.fulltest
	tdata[sb.ext.upper() if sb.ext!="cpp" else "C++"]+=1
	tdata['SM']+=1
	f.close()
	f=open(fn,"w")
	f.write(str(tdata))
	f.close()

def updaterankonequery(sb,user,post):
	if post.testcase.count()==sb.numtest: post.ac+=1
	rank = Rank.query.filter(Rank.user==user.username, Rank.problem==post.id_p).first()
	if rank is None:
		db.session.add(Rank(user=user.username, problem=post.id_p, numsub=1,numtest=sb.numtest,alltest=post.testcase.count()))
	else:
		rank.numsub+=1
		rank.numtest = max(rank.numtest,sb.numtest)
	db.session.commit()

def processtags(s,id_post):
	s=s.lower().replace(' ','').split(',')
	for tag in s:
		if tag=="":continue
		check=Tags.query.filter_by(tagname=tag).first()
		if check is None:
			t=Tags(tagname=tag,user=current_user.username)
			db.session.add(t)
			db.session.commit()
		id_tag=Tags.query.filter_by(tagname=tag).first().id
		check=Tag_post.query.filter(Tag_post.id_tag==id_tag,Tag_post.id_post==id_post).first()
		if check is None:
			tp=Tag_post(id_tag=id_tag,id_post=id_post)
			db.session.add(tp)
			db.session.commit()
def checkmaxsubmit(fn):#kiểm tra số lần nộp bài của user trong bài fn đã vượt quá số lần cho phép hay chưa
	post=Post.query.filter_by(id_p=fn).first()
	pid=post.id
	numsub=Submitcode.query.filter(Submitcode.user==current_user.username,Submitcode.problem==pid).count()
	return (numsub,post.numsub)
def getTimeNow():#Trả về thời gian dạng chuỗi thời gian trong Js
	Month={1:"January",2:"February",3:"March",4:"April",5:"May",6:"June", 
	       7:"July", 8: "August",9:"September",10:"October",11:"November",12:"December"}
	now=datetime.now()
	hour=str(now.hour)
	if now.hour<10: hour="0"+hour
	minute=str(now.minute)
	if now.minute<10: minute="0"+minute
	second=str(now.second)
	if now.second<10: second="0"+second
	day=str(now.day)
	if now.day<10: day="0"+day
	nows=Month[now.month]+" "+day+", "+str(now.year)+" "+hour+":"+minute+":"+second
	return nows
def convertStringToTime(st):#chuyển định dạng chuỗi qua thời gian
	Month={"January":1,"February":2,"March":3,"April":4,"May":5,"June":6, 
	       "July":7, "August":8, "September":9,"October":10,"November":11,"December":12}
	#"June 21, 2021 16:00:00"
	month,day=st.split(",")[0].split()
	month=Month[month]
	day=int(day)
	st=st.split(", ")[1] #2021 16:00:00
	year=int(st.split()[0])
	st=st.split()[1] #16:00:00:00
	h,m,s=st.split(":")
	h,m,s=int(h),int(m),int(s)
	return year,month,day,h,m,s
def conertTimePythontoJavaScript(st):#Chuyển thời gian nhận từ form HTML sang chuỗi trong JavaScript
	#yyyy-MM-ddThh:mm  --> #Tháng ngày, năm giờ:phút:giây (July 02, 2021 12:00:00)
	if st=="" or st is None: return None
	Month={1:"January",2:"February",3:"March",4:"April",5:"May",6:"June", 
	       7:"July", 8: "August",9:"September",10:"October",11:"November",12:"December"}
	year,month,day,hour,minute=str(st.day),st.month,str(st.day),str(st.hour),str(st.minute)
	return Month[int(month)]+" "+day+", "+year+" "+hour+":"+minute+":00"

def conertTimePythontoHTML(st):#
	#Tháng ngày, năm giờ:phút:giây (July 02, 2021 12:00:00) ---> #yyyy-MM-ddThh:mm
	if st=="" or st is None: return None
	year,month,day,hour,minute=str(st.year),str(st.month),str(st.day),str(st.hour),str(st.minute)
	if len(month)==1: month='0'+month
	if len(day)==1: day='0'+day
	if len(minute)==1: minute='0'+minute
	if len(hour)==1: hour='0'+hour
	return year+"-"+month+"-"+day+"T"+hour+":"+minute

def conertTimeHTMLtoPython(st):#Chuyển thời gian nhận từ form HTML sang Python
	#yyyy-MM-ddThh:mm  --> #datetime được truyền ở dạng 'year, month, day, hour, minute, second, microsecond'
	year,month,day,hour,minute=int(st[:4]),int(st[5:7]),int(st[8:10]),int(st[11:13]),int(st[14:])
	return datetime(year,month,day,hour,minute,0,0)

def checkTimeInOnline(ts,te): #Trả về 2 giá trị: (1) cho biết còn trong thời gian làm bài hay không,
												  #: (2) cho biết độ dài của kỳ thi
	
	leng=str(te-ts)[:-3]
	timen=datetime.now()
	if(ts>timen): return -1,leng #Chưa đến giờ
	if timen<=te: return 0,leng # Trong thời gian làm bài
	return 1,leng #Hết giờ

def checkDoituong(tp):#Kiểm tra user thuộc đối tượng tham gia Contest hay không
	if current_user.is_anonymous: return 0
	gu=Groupuser.query.filter(Groupuser.group_id==tp.limit,Groupuser.user_id==current_user.id).first()
	if gu is None: return 0
	return 1

def checkPinC(post):#Kiểm tra bài tập có thuộc Contest nào không? 
				   # Có: Trả về danh sách (các) tags
				   # Không: Danh sách rỗng
	tmp=[]
	for tp in post.tag_id.all():
		tag=Tags.query.filter(Tags.ts!=Tags.te,datetime.now()<=Tags.te,Tags.id==tp.id_tag).first()
		if tag is not None: tmp.append(tag)
	return tmp
def check_user_and_post_inContest(post):
	#Kiểm tra user đang đăng nhập thuộc đối tượng tham gia Contest có bài tập post hay không
	if current_user.is_anonymous: return 0
	PinC=checkPinC(post)
	#print(current_user.username,PinC)
	if len(PinC)==0: return 1
	for tp in PinC:
		if checkDoituong(tp)==1: return 1
	return 0

# def get_accept(username):#lấy danh sách các bài đã accept của 1 user
# 	listidp=[sb.problem for sb in Submitcode.query.filter(Submitcode.user==username,Submitcode.fulltest==1).all()]
# 	listidp=list(set(listidp))
# 	data = []
# 	for idp in listidp:
# 		post = Post.query.filter_by(id=idp).first()
# 		if post is None: continue
# 		data.append([post.id_p,post.id])
# 	return sorted(data,key=lambda x:x[0])
def deletefilecode(folder):
	try:
		for fn in os.listdir(folder):
			if os.path.isdir(os.path.join(folder,fn)):continue
			fname = pathlib.Path(os.path.join(folder,fn))
			subtime=datetime.now()-datetime.fromtimestamp(fname.stat().st_mtime)
			second=subtime.total_seconds()
			tminis=5 if ".log" in fn else 1
			listtmp = [".zip",".jpg",".pdf",".docx",".inp",".out",'.txt']
			for exxt in listtmp:
				if exxt in fn.lower(): tminis=10
			if second>tminis*60: 
				try:
					os.remove( os.path.join(folder,fn))
					print("removed",os.path.join(folder,fn))
				except Exception as e:
					print('cant delete file',fn)
					print(str(e))
					# for p in psutil.process_iter():
					# 	if fn[:-4] in p.name():	p.kill()
	except Exception as e:
		print(str(e))
	return 

@app.context_processor
def returnConfig():
	return {'showtags':app.config['SHOWTAGS'],'domain':app.config['DOMAIN']}
@app.context_processor
def createmenu():
	
	tbegin =time.time()
	menux,menuadmin=[],[]
	menux.append(['homepage/','Trang chủ','primary'])
	menux.append(['tintuc/','Tin tức','primary'])
	menux.append(['listproblem/','Bài tập','primary'])
	menux.append(['listcontest/','Kỳ thi','primary'])
	menux.append(['phanloaibt/','Phân loại','primary'])
	menux.append(['listsubmit/','Bài nộp','primary'])
	menux.append(['hplink/','Shortlink','primary'])
	menux.append(['viewsolution/','Xem code','primary'])
	menux.append(['dethi/','Đề thi HSG','primary'])
	menux.append(['gopde/','Góp đề thi','primary'])
	#menux.append(['themisx/','Themis','danger'])
	menux.append(['giaovien/','Giáo viên','danger'])
	if fhp_permit(["superadmin"]):
		menuadmin.append(['admin_adddoc','Thêm tài liệu','danger'])
		menuadmin.append(['duyetde','Duyệt đề ('+str(dechuaduyet())+')','danger'])
		menuadmin.append(['addde','Thêm đề','danger'])
		menuadmin.append(['resetranking','Reset Ranking','danger'])
		menuadmin.append(['addmark','Cộng điểm và thời gian','danger'])
	if fhp_permit(["admin"]):
		menuadmin.append(['adminproblem','Thêm Bài tập','danger'])
		menuadmin.append(['admin_ql_tintuc','Thêm tin tức','danger'])
		menuadmin.append(['admin_ql_tags','Thêm Tags/Contests','danger'])
		menuadmin.append(['listuser','Quản lý User','danger'])
		menuadmin.append(['addgv','Thêm giáo viên','danger'])
		menuadmin.append(['admin_ql_groups','Quản lý Groups','danger'])
		menuadmin.append(['solvideo','Solution Video','danger'])
		menuadmin.append(['loaitkkhoinhom','Xóa User bị khóa khỏi nhóm','danger'])
		menuadmin.append(['userdiemcao','User điểm cao','danger'])


	fn = "app/static/data/thongke.txt"
	if not os.path.isfile(fn):
		f=open(fn,"w")
		static={'AC':0,'SM':0,'PAS':0,'C++':0,'PY':0}
		static['AC']=Submitcode.query.filter_by(fulltest=1).count()
		static['SM']=Submitcode.query.count()
		static['PAS']=Submitcode.query.filter_by(ext='pas').count()
		static['C++']=Submitcode.query.filter_by(ext='cpp').count()
		static['PY']=Submitcode.query.filter_by(ext='py').count()	
		f.write(str(static))
		f.close()
	f = open(fn,"r")
	static= eval(f.read())
	f.close()
	
	# newpro={}
	# post=Post.query.filter_by(CP=0).order_by(Post.id.desc()).limit(10).all()
	# for p in post:  newpro[p.id_p]=p.id_name
	print("Menu và thống kê",time.time()-tbegin)
	return {'menus':[menux,menuadmin],'static':static}
#Tạo một chuỗi ngẫu nhiên bao gồm các chữ cái và chữ số
def randomtext(length=8, chars=string.ascii_letters + string.digits):
	return ''.join([choice(chars) for i in range(length)])
def initDataBase():
	user = User.query.filter_by(username='admin').first()
	if user is None:
		user = User(username='admin', email='admin@elearning.vn', fullname='Lưu Hải Admin')
		user.set_password('123456')
		user.langdf = "c_cpp"
		db.session.add(user)
		db.session.commit()
	for grname in ["admin"]:
		gr = Groups.query.filter_by(gname=grname).first()
		if gr is not None: continue
		gr = Groups(gname=grname)
		db.session.add(gr)
		db.session.commit()
		user = User.query.filter_by(username='admin').first()
		gru = Groupuser(group_id=gr.id,user_id=user.id)
		db.session.add(gru)
		db.session.commit()
	d={'admin':'admin','superadmin':'admin'}
	for key in d:
		gr=Groups.query.filter_by(gname=key).first()
		if gr is None: continue
		gr.author=d[key]
	
	for tag in Tags.query.all():
		if tag.user is not None: continue
		tag.user='admin'
	db.session.commit()
def docx2html(fndocx,idp): #Chuyển đổi file fndocx của bài tập có mã idp sang html 
	#if not os.path.isfile(fndocx): return ""
	html = pypandoc.convert_file(fndocx, 'html', format='docx', extra_args=["--mathjax"])
	html = html.replace("<table>","<table class='table table-bordered border-dark table-sm w-auto mx-auto'>")	
	html = html.split("\n")[1:]
	html = "\n".join(html)
	# Chỉ thay thế các thẻ <p> bên trong thẻ <td>
	soup = bs(html, "html.parser")
	for td in soup.find_all("td"):
		for pp in td.find_all("p"):
			# Thay thế <p> bằng nội dung của nó + </br>
			new_content = soup.new_string(pp.get_text() + " <br> ")
			pp.replace_with(new_content)
	html = str(soup).replace("&lt;br&gt;","</br>")
	for i in range(1,6):
		si = str(i)
		html = html.replace("media/image"+si+".png","../static/hinhanh/problem/"+idp+si+".jpg")
		html = html.replace("media/image"+si+".jpeg","../static/hinhanh/problem/"+idp+si+".jpg")
		html = html.replace("media/image"+si+".jpg","../static/hinhanh/problem/"+idp+si+".jpg")
	
	return html
def getcodeAC(p):
	getcode = """
		<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-twilight.min.css'>
        <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css'>
        <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/toolbar/prism-toolbar.min.css'>"""
	sbcppx = Submitcode.query.filter(Submitcode.problem==p.id,Submitcode.fulltest==1,Submitcode.ext=="cpp").order_by(Submitcode.timesb.desc()).limit(2).all()
	for sbcpp in sbcppx:
		getcode += "<hr><p class='text-center'><h5 class='text-success'><strong>C++: </strong>Bài làm của <strong>"+sbcpp.user+"</strong></h5></p>"
		getcode += "<pre class='line-numbers'><code class='language-cpp'>"+sbcpp.code.replace("<","&lt;").replace(">","&gt;")+"</code></pre>"

	sbpythonx = Submitcode.query.filter(Submitcode.problem==p.id,Submitcode.fulltest==1,Submitcode.ext=="py").order_by(Submitcode.timesb.desc()).limit(2).all()
	for sbpython in sbpythonx: 
		getcode += "<hr><p class='text-center'><h5 class='text-success'><strong>Python: </strong>Bài làm của <strong>"+sbpython.user+"</strong></h5></p>"
		getcode += "<pre class='line-numbers'><code class='language-python'>"+sbpython.code.replace("<","&lt;").replace(">","&gt;")+"</code></pre>"

	sbpascalx = Submitcode.query.filter(Submitcode.problem==p.id,Submitcode.fulltest==1,Submitcode.ext=="pas").order_by(Submitcode.timesb.desc()).limit(2).all()
	for sbpascal in sbpascalx:
		getcode += "<hr><p class='text-center'><h5 class='text-success'><strong>Pascal: </strong>Bài làm của <strong>"+sbpascal.user+"</strong></h5></p>"
		getcode += "<pre class='line-numbers'><code class='language-pascal'>"+sbpascal.code.replace("<","&lt;").replace(">","&gt;")+"</code></pre>"
	getcode += """
		<script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js'></script>
			<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-clike.min.js"></script>
			<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-c.min.js"></script>
            <script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js'></script>
            <script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-cpp.min.js'></script>
            <script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-pascal.min.js'></script>
            <script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js'></script>
            <script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/toolbar/prism-toolbar.min.js'></script>
            <script src='https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/copy-to-clipboard/prism-copy-to-clipboard.min.js'></script>"""
	return getcode
def getProblem(p,listc):
	sol = ""
	if p.sol is not None and current_user.is_authenticated and current_user.giaovien==1:
		fnsol="app/static/download/"+p.id_p+"_sol.docx"
		if not os.path.isfile(fnsol):
			fsol = open(fnsol,"wb")
			fsol.write(p.sol)
			fsol.close()
		sol = docx2html(fnsol,p.id_p)
	if current_user.is_authenticated and current_user.giaovien==1: sol += getcodeAC(p)	
	problem={
	"id":p.id,
	"id_p":p.id_p,
	"id_name":p.id_name.upper(),
	"body":str(p.body).replace("\\n","</br>") if p.docx is not None else str(p.body).replace("\r","\\n").replace("\\n","\n"),
	"tmpcode": "",
	"filelogs":"",
	"ext":"",
	"activate":False,
	"tags":[],
	"alltestcase":[],
	"conf":Config.query.filter_by(idp=p.id).first(),
	"source":p.source,
	"pdf":p.pdf,
	"yt":p.yt,
	"docx":p.docx,
	"sol":sol
	}
	problem["imgbase64"]=p.imgbase64 if p.imgbase64 is not None else 0
	if p.pdf is not None:
		fn="app/static/download/"+p.id_p+".pdf"
		f=open(fn,"wb")
		f.write(p.pdf)
		f.close()
		put_watermark(fn, fn, "app/static/WM_hpcode.pdf")
	#if fhp_permit(['admin'])==0: problem['source']=None
	tmpd={}#{"&lt;":"<","&gt;":">"}
	for key in tmpd: problem['body']=problem['body'].replace(key,tmpd[key])
	problem['body']=markdown.markdown(problem['body'])
	if p.testcase.count()==0: problem['body']="<span class='text-danger'><b> Bài tập chưa có test</b></span>\n"+problem['body']
	problem['body']=problem['body'].replace("</code>","</code> </pre>")
	problem['body']=problem['body'].replace("<code>","<pre><code>")
	problem['body']=problem['body'].replace("<br>","")
	
	if len(listc)>0 and listc[0].tagname in ["NoContest","chuyentin237","hsga","shgb"]: #Bài tập không thuộc Contest thì có Phân loại bài tập và TestCase
		for tag_id in p.tag_id.all():
			tgx=Tags.query.filter_by(id=tag_id.id_tag).first()
			if tgx is None: continue
			problem['tags'].append(tgx.tagname)
	return problem
def getlistvideoPlaylist(linkpl):
	pathdata="app/static/videoth/data.txt"
	if not os.path.isfile(pathdata):
		f=open(pathdata,"w",encoding="utf-8"); f.write(""); f.close()
	f=open(pathdata,"r",encoding="utf-8"); datatmp=f.read().split("\n"); f.close()
	dataf=[d.split(" || ")[0] for d in datatmp]

	pl=Playlist(linkpl['link'])
	for url in pl.video_urls:
		if url.split("=")[1] in dataf: continue
		
		f=open(pathdata,"a",encoding="utf-8")
		yt=YouTube(url)
		ys=yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
		ys.download("app/static/videoth/")
		os.rename("app/static/videoth/"+ys.default_filename, "app/static/videoth/"+url.split("=")[1]+".mp4")
		f.write(url.split("=")[1]+" || "+yt.title+" || "+linkpl['name']+" "+linkpl['sach']+"\n")
		f.close()

#Lấy tất cả các Tag của bài tập
def getalltag(p):
	tmp=[]
	for tp in p.tag_id.all():
		tag=Tags.query.filter_by(id=tp.id_tag).first()
		if tag.ts==tag.te: tmp.append(tag.tagname)
	return tmp

def updateinforvideo(idv):
	if idv is None: return
	url="https://www.youtube.com/watch?v="+idv
	try:
		yt=YouTube(url)
		vid=Videohp.query.filter_by(idv=idv).first()
		vid.views=yt.views
		vid.descr=yt.description
		db.session.commit()
	except:
		print("err")

def numviewtestcase():
	import time
	result = User_tests.query.count()
	return result
def hpranking(cname):
	rootdir="app/static/rankingc/"
	tag = Tags.query.filter_by(tagname=cname).first()
	if tag is None: return
	pro = get_all_post_in_tag(cname) # Lấy tất cả các id của bài tập trong Contest có mã tagname=cname
	user = get_all_user_in_tag(cname) # Lấy tất cả các username của đối tượng tham gia Contest có mã tagname=cname
	extentions = ["","py","cpp","pas"]
	tpost,tuser,tdata,tdata_ext=[],{},{},{}
	for extmp in extentions: tdata_ext[extmp]={}
	for p in pro:
		post = Post.query.filter_by(id=p).first()
		#tp = Tag_post.query.filter_by(id_post=p).first()
		tp = Tag_post.query.filter(Tag_post.id_tag==tag.id,Tag_post.id_post==p).first()
		#if tp.no is None: tp.no=0;db.session.commit()

		tpost.append([tp.no,post.id_p])
		
	tpost=sorted(tpost, key=lambda x: x[0])
	for username in user: 
		tuser[username]=User.query.filter_by(username=username).first().fullname
		tdata[username]={}
	for pid in pro:
		post = Post.query.filter_by(id=pid).first()
		maxpoint = Tag_post.query.filter(Tag_post.id_tag==tag.id,Tag_post.id_post==pid).first().point
		if maxpoint is None: maxpoint = 10
		for username in user:
			submit = Submitcode.query.filter(Submitcode.user==username,Submitcode.problem==pid,Submitcode.timesb<=tag.te).order_by(Submitcode.numtest.desc())
			
			if submit.count()==0: continue
			if submit.first() is None: continue
			tdata[username][post.id_p]=[0,0,0]
			ext = submit.first().ext
			point=round(submit.first().numtest/post.testcase.count()*maxpoint,2)
			tdata[username][post.id_p]=[point,submit.count(),submit.first().numtest==post.testcase.count()] #điểm, số lần nộp, fulltest
			if username not in tdata_ext[ext]: tdata_ext[ext][username]={}
			tdata_ext[ext][username][post.id_p]=[point,submit.count(),submit.first().numtest==post.testcase.count()] #điểm, số lần nộp, fulltest
		
	for ex in extentions:
		fn = rootdir+cname+"_"+ex+".txt"
		if ex == "": fn = rootdir+cname+".txt"
		f=open(fn,"w",encoding="utf-8")
		f.write(str(tpost)+"\n")
		f.write(str(tuser)+"\n")
		if ex == "": f.write(str(tdata))
		if ex != "": f.write(str(tdata_ext[ex]))
		f.close()
	return 
def remove_tags(text): #Xóa thẻ HTML trong xâu
    # Compile the regex once for efficiency
    CLEANR = re.compile('<.*?>')
    cleantext = re.sub(CLEANR, '', text)
    return cleantext

def getStatisContest(cname):
	tongdiemmax = 0 #Tổng điểm tối đa của tất cả các bài tập trong Contest
	tongdiem = 0 #Tổng điểm mà user đạt được
	if current_user.is_anonymous: return 0
	
	tag = Tags.query.filter_by(tagname=cname).first()
	if tag is None: return 0
	for p in tag.post_id.all():
		tp=Tag_post.query.filter_by(id=p.id).first()
		tongdiemmax+=tp.point
		post = Post.query.filter_by(id=tp.id_post).first()
		r = Rank.query.filter(Rank.user==current_user.username,Rank.problem==post.id_p).first()
		if r is None: continue
		tongdiem+=r.numtest/r.alltest*tp.point

	return round(tongdiem/tongdiemmax*100,2)
def writelogerr(e):
	f=open("Error.txt","a",encoding="utf-8")
	f.write("\n\n"+str(e)+"\n\n")
	f.close()
	print(str(e))
def numDethi(makythi):#Lấy số lượng đề thi mỗi loại theo mã
	return Dethi.query.filter(Dethi.makythi==makythi, Dethi.check==1).count()
def numview_testcase():
	if current_user.is_anonymous: return 0
	if fhp_permit(["admin","superadmin"])==1: return 10000
	if current_user.giaovien==1: return 100
	if Giaovienhs.query.filter_by(hs_id=current_user.id).first() is not None: return 10
	return 0
def ctc():#Code tích cực trong 1 ngày, 7 ngày, 30 ngày
	betime = time.time()
	fname = "app/static/data/codetichcuc.txt"
	tmp = [{},{},{}]#{"user":"","ac":0,total:0}
	
	if datetime.now().second <=3 or not os.path.isfile(fname):
		sball = Submitcode.query.filter(Submitcode.timesb>=datetime.now()-timedelta(days=30)).all()
		
		for sb in sball:
			if sb.timesb>=datetime.now()-timedelta(days=7):
				if sb.user not in tmp[1]: tmp[1][sb.user]={"ac":0,"total":0}
				tmp[1][sb.user]["total"]+=1
				if sb.fulltest==1: tmp[1][sb.user]["ac"]+=1

			if sb.user not in tmp[2]: tmp[2][sb.user]={"ac":0,"total":0}
			tmp[2][sb.user]["total"]+=1
			if sb.fulltest==1: tmp[2][sb.user]["ac"]+=1
		
		f = open(fname,"w",encoding='utf-8')
		for i in range(3):
			ltmp = [[k, tmp[i][k]['ac'],tmp[i][k]['total']] for k in tmp[i]]
			tmp[i] = sorted(ltmp, key=lambda x: x[1],reverse=True)[:3]
			f.write(str(tmp[i])+"\n")
		f.close()
		
	f = open(fname,"r",encoding='utf-8')
	tmp=[eval(d) for d in f.read().split("\n")[:3]]
	f.close()
	tmpx={}
	sball = Submitcode.query.filter(Submitcode.timesb>=datetime.now()-timedelta(days=1)).all()
	for sb in sball:
		if sb.user not in tmpx: tmpx[sb.user]={"ac":0,"total":0}
		tmpx[sb.user]["total"]+=1
		if sb.fulltest==1: tmpx[sb.user]["ac"]+=1
	ltmp = [[k, tmpx[k]['ac'],tmpx[k]['total']] for k in tmpx]
	tmp[0] = sorted(ltmp, key=lambda x: x[1],reverse=True)[:3]
	print("Code tích cực",time.time()-betime)
	return tmp
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
#btdexuat = baitapdexuat(current_user.username)# Bài tập đề xuất cho user
def taidethi_function(idx,username):
	fname = "app/static/chambai/tmp/dethi_"+str(idx)+".txt"
	def ghilog(st):
		f=open(fname,"a",encoding="utf-8")
		f.write(st)
		f.close()
	dethi=Dethi.query.filter_by(id=idx).first()
	year2 = dethi.year2
	if dethi.kythi == "Olympic 30/4": year2 = str(dethi.year2).split("-")[1]
	namef="["+username+"]["+year2+"]["+no_accent_vietnamese(dethi.kythi).replace("/","-")+"]["+no_accent_vietnamese(dethi.tinh).replace(" ","")+"]"
	folder_n = os.path.join("app/static/chambai/tmp/",namef)
	if not os.path.exists(folder_n): os.makedirs(folder_n)
	if not os.path.exists(folder_n+"/[code]"): os.makedirs(folder_n+"/[code]")
	#zip = ZipFile(folder_n + '.zip', 'w', ZIP_DEFLATED)

	#Ghi đề thi docx
	if dethi.dedocx is not None:
		namedocx=folder_n+"/"+namef+".docx"
		f=open(namedocx,"wb"); f.write(dethi.dedocx); f.close()
		#zip.write(namedocx,namef+".docx")
		ghilog("<b>Đang tạo tệp Đề thi: "+namef+".docx</b>\n")
		time.sleep(1)

	#Ghi đề thi pdf
	if dethi.depdf is not None:
		namedocx=folder_n+"/"+namef+".pdf"
		f=open(namedocx,"wb"); f.write(dethi.depdf); f.close()
		#zip.write(namedocx,namef+".pdf")
		ghilog("<b>Đang tạo tệp Đề thi: "+namef+".pdf</b>\n")
		time.sleep(1)
	
	#ghi solution
	if dethi.sol is not None:
		namedocx=folder_n+"/"+namef+"_sol.docx"
		f=open(namedocx,"wb"); f.write(dethi.sol); f.close()
		#zip.write(namedocx,namef+"_sol.docx")
		ghilog("<b>Đang tạo tệp Hướng dẫn:"+namef+"_sol.docx</b>\n")
	#Code của tất cả các bài
	for idpost in dethi.post_id.all(): #Duyệt các id trong Dethi_post
		post=Post.query.filter_by(id=idpost.id_post).first()
		idp=post.id_p
		sbx= Submitcode.query.filter(Submitcode.problem==post.id,Submitcode.numtest==post.testcase.count())
		ghilog("Đang tạo "+str(sbx.count())+" tệp chương trình của bài: <b>"+idp+"</b>")
		runx = 1
		time.sleep(1)
		for sb in sbx.all():
			time.sleep(0.1)
			nzipin="[code]/["+idp+"]["+ str(sb.id)+"]["+sb.user+"]."+sb.ext
			testf=os.path.join(folder_n,nzipin)
			f=open(testf,"w",encoding='utf-8'); f.write(sb.code); f.close()
			#zip.write(testf,nzipin)
			if runx%max((sbx.count()//5),1)==0:ghilog(str(runx)+"-") 
			elif runx%3==0: ghilog("-") 
			runx+=1
			#ghilog("-----"+nzipin+"\n")
		ghilog(" \n")
	#testcase của tất cả các bài trong kỳ thi
	if not os.path.exists(folder_n+"/[tests]"): os.makedirs(folder_n+"/[tests]")
	for idpost in dethi.post_id.all(): #Duyệt các id trong Dethi_post
		post=Post.query.filter_by(id=idpost.id_post).first()
		prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else "0-9"
		fntestpost = app.config["TESTCASE"]+prefix+"/"+post.id_p+".zip" #file test của bài tập
		#os.chmod(fntestpost, 0o666)
		ghilog("Tạo bộ tests bài: <b>"+post.id_p+"</b>\n")
		#shutil.copytree(fntestpost, folder_n+"/[tests]/"+post.id_p, dirs_exist_ok=True)
		shutil.copyfile(fntestpost, os.path.join(folder_n, "[tests]", post.id_p + ".zip"))
	try:
		ghilog("Đang nén Đề thi:...")
		shutil.make_archive(folder_n, 'zip', folder_n)
		ghilog("Xong\n")
		shutil.rmtree(folder_n)
	except Exception as e:
		print(e)
	link=os.path.join("https://hpcode.edu.vn",folder_n[4:]+".zip")
	ghilog("<span class='text-success'><b>Đã tạo xong</b></span>\n")
	ghilog("<a href=\'"+link+"\'>click vào đây để tải về</a><br>")
	ghilog("Hoặc copy "+"<a href=\'"+link+"\'>"+link+"</a> vào trình duyệt")
def contains_system_command(code):
	return False
    # try:
    #     subprocess.run(code, shell=True, check=True)
    #     return True
    # except subprocess.CalledProcessError:
    #     return False
def baitapdexuat(username): #đề xuất 10 bài tập cho 1 người
	#Chạy code lần đầu với user admin: cần phải bỏ hết Comment ở dưới để reset lại dữ liệu (bảng Rank và post.ac - số lượt nộp đúng)
	#Sau đó Comment lại rồi chạy lại code
	# if fhp_permit(["admin"])==1:
	# 	for r in Rank.query.all():db.session.delete(r)
	# 	db.session.commit()
	
	if Rank.query.count()==0 and fhp_permit(["admin"])==1: # Cập nhật Class Rank
		# for p in Post.query.all(): 
		# 	p.ac=0
		# 	db.session.commit()
		# for p in Post.query.all(): 
		# 	p.ac=Submitcode.query.filter(Submitcode.problem==p.id,Submitcode.fulltest==1).count()
		# db.session.commit()	
		#print("chạy lại code")
		cnt = 0
		for sb in Submitcode.query.all():
			cnt +=1
			if cnt%100==0: print(cnt)
			post = Post.query.filter_by(id=sb.problem).first()
			if post is None: continue
			tmp = Rank.query.filter(Rank.user==sb.user,Rank.problem==post.id_p).first()
			if tmp is None:
				rank = Rank(user=sb.user,problem=post.id_p,numtest=0,alltest=post.testcase.count(),numsub=0)
				db.session.add(rank)
		db.session.commit()
		cnt = 0
		for sb in Submitcode.query.all():
			if sb.numtest is None: continue
			cnt +=1
			if cnt%100==0: print(cnt)
			post = Post.query.filter_by(id=sb.problem).first()
			if post is None: continue
			tmp = Rank.query.filter(Rank.user==sb.user,Rank.problem==post.id_p).first()
			tmp.numtest=max(tmp.numtest,sb.numtest)
			tmp.numsub+=1
		db.session.commit()
	
	listac = [pr.problem for pr in Rank.query.filter(Rank.user==username, Rank.alltest==Rank.numtest).all()]
	listac.sort()
	
	allpost = Post.query.filter(Post.id_p.not_in(listac)).order_by(Post.ac.desc()).limit(10)
	
	return [[p.id_p,p.id_name] for p in allpost]
def dechuaduyet(): #Đề chưa duyệt
	return 	Dethi.query.filter_by(check=0).count()
def slac(user): #Tính số lượng bài đã AC của user
	if user.is_anonymous: return 0
	return Rank.query.filter(Rank.user==user.username,Rank.numtest==Rank.alltest).count()
app.jinja_env.globals.update( fhp_permit=fhp_permit,conertTimePythontoHTML=conertTimePythontoHTML,numviewtestcase=numviewtestcase,getStatisContest=getStatisContest)
app.jinja_env.globals.update( numDethi=numDethi,ctc=ctc,btdexuat=baitapdexuat,dechuaduyet=dechuaduyet,solannpbaiconlai=solannpbaiconlai)
app.jinja_env.globals.update( Imagebase64=Imagebase64, slac=slac,haveads=haveads)
