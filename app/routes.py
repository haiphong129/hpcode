from app import app
from flask import Flask, render_template, redirect, url_for, request, session,flash, jsonify, Response
from flask_login import current_user, login_user, logout_user, login_required
from app.models import * #User, Yeucaugv, Post, Exam, Contest, Contest_post, History,Submitcode
#from datetime import datetime,timezone
import datetime, time
from datetime import timedelta
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import os
from pytube import Playlist, YouTube
import string
from googletrans import Translator
import csv, pandas
from flask import send_from_directory
from hpfunction import *
import markdown
import requests, random
from zipfile import ZipFile, ZIP_DEFLATED 
from flask_simplemde import SimpleMDE
import base64
import shutil
import multiprocessing
import docx2pdf
from urllib.parse import urlparse
from hpjudle import *
import locale
#import pypandoc
locale.setlocale(locale.LC_ALL, 'vi_VN')
app.app_context().push()
random.seed(47)
from flask_simple_captcha import CAPTCHA
YOUR_CONFIG = {
    'SECRET_CAPTCHA_KEY': 'LONG_KEY',
    'CAPTCHA_LENGTH': 6,
    'CAPTCHA_DIGITS': False,
    'EXPIRE_SECONDS': 600,
}
SIMPLE_CAPTCHA = CAPTCHA(config=YOUR_CONFIG)
app = SIMPLE_CAPTCHA.init_app(app)
@app.route("/",methods=['GET', 'POST'])
@app.route("/<string:menu>",methods=['GET', 'POST'])
def index(menu=None):
	initDataBase()
	if request.method == 'POST':
		if "login" in request.form:
			return redirect('/login/')
		if "signup" in request.form:
			return redirect('/signup/')
	if menu is None: menu='homepage'
	return redirect('/'+menu)
hpqueue = multiprocessing.Queue()
@app.before_request
def before_request():
	url = request.url
	if "logout" in url: return 
	if "xacthuctaikhoan" in url: return 
	if current_user.is_authenticated:
		if current_user.giaovien==1: 
			current_user.thoihan = datetime.now() + timedelta(days=365)
			current_user.khoatk=0
			db.session.commit()
		if current_user.thoihan < datetime.now():
			current_user.khoatk=1
			for u in Giaovienhs.query.filter_by(hs_id=current_user.id).all():
				db.session.delete(u)
			db.session.commit()
			
	deletefilecode('app/static/chambai/tmp')
	deletefilecode('app/static/download')
	session['meta']={"title":"hpcode.edu.vn","des":app.config['ABOUT'],"url":request.url,"img":"https://hpcode.edu.vn/static/hinhanh/lhp.jpg"}
	if "%23" in url:
		return redirect(url.replace("%23","#"), code=301)
	
	tmp = urlparse(request.url)
	urlx = tmp.scheme +"://"+tmp.netloc + "/"
	url= url.replace(urlx,"").replace("%5B","[").replace("%5D","]")
	if "static/chambai/tmp/[" in url:
		utm= url.replace("static/chambai/tmp/[","")
		utm = utm.split("][")[0]
		
		if current_user.is_anonymous or utm!=current_user.username: 
			return render_template('error.html',messeg="Thao tác của bạn không được phép")
	
	url = url.split("/")[0]
	url = url.split("?")[0]
	if url not in app.config["ALLOW_ROUTE"]:
		print(url)
		return redirect (url_for('viewlink',key=url))
@app.route("/homepage/",methods=['GET', 'POST'])
def homepage():	
	
	dethi=[]
	for d in Dethi.query.filter(Dethi.check<2).order_by(Dethi.id.desc()).limit(5).all():
		if d.kythi=="HSG Chọn đội tuyển": d.kythi="HSG Chọn Đội tuyển"
		if d.notetitle is None: d.notetitle=""
		#ctai = Dethiuser.query.filter_by(id_dethi=d.id).count()
		year2 = d.year2
		if d.kythi == "Olympic 30/4": year2 = str(d.year2).split("-")[1]
		luotxem = 0 if d.luotxem is None else d.luotxem
		dtmp = {"kythi":d.kythi,"tinh":d.tinh,"namhoc":year2,"nguoigop":d.username,"idde":d.id,"stt":d.check,"luotxem":luotxem,"notetitle":d.notetitle}
		dethi.append(dtmp)
	
	pro = []
	for p in Post.query.filter_by().order_by(Post.id.desc()).limit(10).all():
		tmp = {}#getProblem(p,[])
		#if len(p.body)<=100: continue
		tmp["id_name"]=p.id_name
		tmp["id_p"]=p.id_p
		tmp['imgbase64']=0
		tmp["body"]=p.body if p.body is not None else ""
		pro.append(tmp)
		#if len(pro)==5: break
	

	newfirst=News.query.order_by(News.times.desc()).limit(1).first()
	newfirst=News.query.filter_by(id=46).first()
	tintuc={"title":"Không có tin tức","content":"","auther":"","time":"","id":None}
	if newfirst is not None:
		tintuc["id"]=newfirst.id
		tintuc["title"]=newfirst.title
		tintuc["content"]=markdown.markdown(newfirst.content.replace("amp;",""))
		tintuc["auther"]=User.query.filter_by(id=newfirst.user_id).first().username
		tintuc["time"]=newfirst.times
	

	return render_template("homepage.html",dethi=dethi,pro=pro,tintuc=tintuc)
@app.route("/editlink/",methods=['GET', 'POST'])
def editlink():	
	status =""
	data={'link':"",'title':"",'shortlink':"",'timewait':""}
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	key = request.args.get('key')
	link = Shortlink.query.filter_by(key=key).first()
	if link is not None: data={'link':link.link,'title':link.title,'shortlink':link.key,'timewait':link.timewait}
	if request.method == 'POST':
		data['link'] = request.form['link']
		data['title'] = request.form['title']
		data['timewait'] = request.form['timewait']
		data['shortlink'] = key
		link = Shortlink.query.filter_by(key=data['shortlink']).first()
		if link is None: return render_template('error.html',messeg="Link rút gọn không tồn tại")
		link.link=data["link"]
		link.title = data['title']
		link.timewait=data["timewait"]
		db.session.commit()
		status = "<span class='text-success'>Thành công</span>"
	return render_template('editlink.html',data=data,status=status)

@app.route("/viewlink/",methods=['GET', 'POST'])
def viewlink():
	datalink=[]
	cnt = 0
	for link in Shortlink.query.order_by(Shortlink.timeb.desc()).all():
		if random.randint(1,10)==2:
			titlelink = link.title if ".zip" not in link.title else "<b>Bộ test bài <a href='https://hpcode.edu.vn/viewctpr/?idp="+link.title.split()[0]+"'>"+link.title.split()[0]+"<b></a>"
			datalink.append({'title':titlelink,'shortlink':link.key,'sl':link.sl,'timewait':link.timewait})
			cnt+=1
		if cnt==11: break
			
	key = request.args.get('key')
	if "?" in key: key = key.split("?")[0]
	username = current_user.username if current_user.is_authenticated else ""#request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
	fcheck = "app/static/chambai/tmp/"+username+"_"+key+".txt"
	if not os.path.isfile(fcheck): f=open(fcheck,"w"); f.close()
	link = Shortlink.query.filter_by(key=key).first()
	if link is None: return render_template('error.html',messeg="Thao tác của bạn không được phép")
	session['meta']["title"]="hpcode.edu.vn - "+link.title
	fname = pathlib.Path(fcheck)
	subtime=datetime.now()-datetime.fromtimestamp(fname.stat().st_mtime)
	second=subtime.total_seconds()
	if second+3<link.timewait:
		return render_template("viewlink.html",link=None,timewait=link.timewait,key=key,domain=app.config['DOMAIN'],titlelink=link.title,datalink=datalink)
	if os.path.isfile(fcheck): os.remove(fcheck)
	link.sl+=1
	import math
	link.timewait= int(math.log(link.sl)*10)//2
	db.session.commit()
	response = requests.head(link.link, allow_redirects=False, timeout=2)   #kiểm tra link còn sống hay không
	link.stl="text-danger" if response.status_code>400 else "text-success" #Nếu còn sống thì title màu xanh trong https://DOMAIN/shortlink
	print(response.status_code)
	db.session.commit()
	return render_template('viewlink.html',link=link.link,key=key,domain=app.config['DOMAIN'],titlelink=link.title,datalink=datalink)

@app.route("/donate/",methods=['GET', 'POST'])
def donate():
	return render_template('donate.html')

@app.route("/multiads/",methods=['GET', 'POST'])
def multiads():
	return render_template('multiads.html')

@app.route("/xacthuctaikhoan",methods=['GET', 'POST'])
@login_required
def xacthuctaikhoan():
	
	session['meta']['title']="Xác thực tài khoản - hpcode.edu.vn"
	if current_user.solangui is None: current_user.solangui=0
	note = "Bạn còn <span class='text-danger'><b>"+str(10-current_user.solangui)+"/10</b></span> lần xác thực!<br>"
	if current_user.xacthuc==1: return redirect('tintuc')
	data={'username':current_user.username,'email':current_user.email,'solangui':current_user.solangui}
	if current_user.solangui>=10:
		note = "Tài khoản của bạn bị khóa vì bạn gửi gửi xác thực quá nhiều lần!"
		return render_template('xacthuctaikhoan.html',data=data,note=note)
	if request.method == 'POST':
		if request.form['submit']=="Xác thực":
			current_user.solangui+=1
			data['solangui']+=1
			db.session.commit()
			chuoixacthuc  = request.form['chuoixacthuc']
			if chuoixacthuc == current_user.maxacthuc: 
				current_user.xacthuc=1
				db.session.commit()
				return redirect("tintuc")
			else: note = "Chuỗi xác thực bạn gửi không đúng. Nhập lại!<br>Bạn còn <span class='text-danger'><b>"+str(10-current_user.solangui)+"/10</b></span> lượt xác thực."
		if request.form['submit']=="Gửi lại chuỗi xác thực":
			email  = request.form['email']
			if email!=current_user.email: 
				note = "<span class='text-success'>Đã cập nhật email</span><br>"
				checkemail = User.query.filter_by(email=email).first()
				if checkemail is not None:
					note = "Email <span class='text-danger'>"+email+"</span> đã có. Hãy nhập Email khác"
					return render_template('xacthuctaikhoan.html',data=data,note=note)
				current_user.email = email
			data['email']=current_user.email
			current_user.maxacthuc = randomtext(20,string.ascii_lowercase)
			db.session.commit()
			result = sent_email_xacthuc(current_user)
			if result.json()['Messages'][0]['Status']!="success":
				note = "Tôi đã có gắng gửi cho bạn một Email chứa mã xác thực nhưng có thể bạn không nhận được. Hãy quay lại vào ngày mai!"
			else:
				note+="<span class='text-success'><b>Đã gửi lại chuỗi xác thực.</b></span><br>Hãy kiểm tra Email (gồm cả Spam và thư rác)!"
	return render_template('xacthuctaikhoan.html',data=data,note=note)

@app.route("/chinhsach",methods=['GET', 'POST'])
def chinhsach():
	session['meta']['title']="hpcode - Chính sách"
	return render_template('chinhsach.html')
@app.route("/ads.txt")
def point_to_ads():
	return send_from_directory("static", "ads.txt")

@app.route("/sitemap.xml")
def point_to_sitemap():
	return send_from_directory("static", "sitemap.xml")

@app.route("/sw.js")
def point_to_sw():
	return send_from_directory("static", "sw.js")
@app.route("/robots.txt")
def point_to_robots():
	return send_from_directory("static", "robots.txt")
@app.route("/.well-known/pki-validation/E6023A75BBB88CB17784C5FFAA283C6C.txt")
def point_to_ssl():
	
	try:
		return send_from_directory("static", "ssl.txt")
	except Exception as e: writelogerr(e)
	return render_template('error.html',messeg="Có lỗi")

@app.route("/favicon.ico")
def point_to_favicon():
	return send_from_directory("static", "favicon.ico")

@app.route("/downloadfiledoc/",methods=['GET', 'POST'])
@login_required
def downloadfiledoc():
	session['meta']['title']="hpcode - Tải file word"
	try:
		slug = request.args.get('slug')
		session['meta']['title']="hpcode -"+slug
		fn = request.args.get('fn')
		doc=Document.query.filter_by(slug=slug).first()
		diem=doc.diem
		ext=os.path.splitext(fn)[1]
		
		if ext==".exe": diem=0
		if ext==".docx": diem=diem*5
		if ext==".pptx": diem=diem*10
		if fhp_permit(['superadmin'])==1: diem=0
		if current_user.ndow<diem: return render_template("error.html",messeg="Bạn không đủ điểm để tải tệp "+ fn)
		current_user.ndow=current_user.ndow-diem
		db.session.commit()
		root=os.path.join("app/static/document",doc.lop,doc.slug,fn)
		copyfile(root,os.path.join("app/static/download",fn))
		#link=os.path.join(app.config['DOMAIN'],"static/download/",fn)
		return render_template('download.html',link=os.path.join("../static/download/",fn))
	except Exception as e: writelogerr(e)
	return render_template('error.html',messeg="Có lỗi")
@app.route("/listdoc/",methods=['GET', 'POST'])
def listdoc():
	session['meta']['title']="hpcode - Tài liệu"
	if 1==1:
		page = request.args.get('page', 1, type=int)
		slug = request.args.get('tag')
		data=Document.query.filter_by(slug=slug).first()
		if data is None:
			data=Document.query.order_by(Document.id.desc()).first()
		data.luotxem=data.luotxem+1
		db.session.commit()
		data.noidung=markdown.markdown(data.noidung).replace("hpcode.pro","hpcode.edu.vn")
		data.gioithieu=data.gioithieu.replace("lqdonkh.xyz","hpcode.edu.vn")
		allfile=get_all_file_in_doc(data)
		fileimage,filedown=[],[]
		for i in range(len(allfile)): 
			if allfile[i][-3:].lower() in ['jpg','png']:
				fileimage.append(os.path.join(app.config['DOMAIN'],"static/download/",data.slug+"_"+allfile[i]))
			else:
				filedown.append(allfile[i])
		doc=Document.query.order_by(Document.id.desc()).paginate(page=page,per_page=10)
		return render_template("listdoc.html",data=data,filedown=filedown,fileimage=fileimage,doc=doc.items,page=page,lastpage=doc.pages,User=User)
	
	return render_template('error.html',messeg="Có lỗi")
@app.route("/admin_deldoc/",methods=['GET', 'POST'])
@login_required
def admin_deldoc():
	if fhp_permit(["superadmin"])==0:
		return render_template("error.html",messeg="Không có quyền truy cập")
	slug=request.args.get("slug")
	slugmain=request.args.get("slugmain")
	doc=Document.query.filter_by(slug=slug).first()
	db.session.delete(doc)
	db.session.commit()
	return redirect (url_for('listdoc',tag=slugmain))
@app.route("/admin_adddoc/",methods=['GET', 'POST'])
@login_required
def admin_adddoc():
	session['meta']['title']="hpcode - Thêm tài liệu"
	if fhp_permit(["superadmin"])==0:
		return render_template("error.html",messeg="Không có quyền truy cập")
	slug=request.args.get("slug")
	doc=Document.query.filter_by(slug=slug).first()
	slugall=[ doc.slug for doc in Document.query.all()]
	if request.method == 'POST':
		tieude = request.form['tieude']
		slug = no_accent_vietnamese(tieude)
		congkhai = (request.form.get('congkhai') is not None) and True
		lop = request.form['lop']
		diem = int(request.form['diem'])
		gioithieu = request.form['gioithieu'].replace("\n","<br>")
		noidung = request.form['noidung']
		
		while("<br><br>" in gioithieu): gioithieu=gioithieu.replace("<br><br>","<br>")
		
		uploadfiledoc(request.files.getlist("file[]"),lop,slug)
		doc=Document.query.filter_by(slug=slug).first()
		if doc is None:
			doc=Document(tieude=tieude,slug=slug,congkhai=congkhai,lop=lop,diem=diem,gioithieu=gioithieu,noidung=noidung,user_id=current_user.id)
			db.session.add(doc)
		else:
			doc.tieude,doc.slug=tieude,slug
			doc.congkhai=congkhai
			doc.lop,doc.diem=lop,diem
			doc.gioithieu,doc.noidung=gioithieu,noidung
			doc.user_id=current_user.id
		db.session.commit()
	imageall=get_all_file_in_doc(doc)
	tmpd={"\r\n":"\\n","\n":"\\n","lqdonkh.xyz":"hpcode.edu.vn"}
	if doc is not None:
		for key in tmpd: doc.noidung=doc.noidung.replace(key,tmpd[key])
	return render_template('admin_adddoc.html',doc=doc,slugall=slugall,imageall=imageall)

@app.route("/admin_delfile/",methods=['GET', 'POST'])
@login_required
def admin_delfile():#Xóa 1 file trong doc
	
	slug = request.args.get('slug')
	fn = request.args.get('fn')
	doc=Document.query.filter_by(slug=slug).first()
	root=os.path.join("app/static/document",doc.lop,doc.slug)
	if os.path.splitext(fn)[1] in ['.jpg','.png']: root=os.path.join(root,"image")
	root=os.path.join(root,fn)
	if os.path.isfile(root): os.remove(root)
	root=os.path.join("app/static/download",fn)
	if os.path.isfile(root): os.remove(root)
	return redirect (url_for('admin_adddoc',slug=slug))
@app.route("/slviewcode/<string:info>",methods=['GET', 'POST'])
@app.route("/slviewcode/",methods=['GET', 'POST'])
def slviewcode(info=None):
	code = Submitcode.query.filter_by(id=int(info)).first()
	if(current_user.username!=code.user):
		check,_=checkPinC(code.problem)
		if (check<=0 and fhp_permit(["superadmin","admin"])==0 ): 
			return render_template('error.html',messeg="Không thể xem Code khi Contest chưa kết thúc.",data=None)
	if code is None: return "Có lỗi trong quá trình xử lý"
	post=Post.query.filter_by(id=code.problem).first()
	tmpcode=code.code
	tmp={'<':'&lt;','>':'&gt;'}
	for key in tmp: tmpcode=tmpcode.replace(key,tmp[key])
	fn='app/static/download/'+info+str(random.randint(0,1000))+'.'+code.ext+'.html'
	f=open(fn,'w')
	f.write('''<html>
			   <head>
    			<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KyZXEAg3QhqLMpG8r+8fhAXLRk2vvoC2f3B09zVXn8CA5QIVfZOJ3BCsw2P0p/We" crossorigin="anonymous">
			   </head>
			   <body >
					<div class="row justify-content-center m-1 p-1">
    					<div class="col-md-auto m-1 p-1">
							<script src="https://cdn.rawgit.com/google/code-prettify/master/loader/run_prettify.js"></script>
								<pre class="prettyprint"><h6>'''+tmpcode.replace('\n','')+"</h6></pre></div></div></body></html>")
	f.close()
	link=app.config['DOMAIN']+fn[3:]
	getapi=requests.get('https://mmo1s.com/api?api=4952a1fed05ddbbadf6116769c3b0c3124d00cad&url='+link)
	if getapi.json()['status']=='success': link = getapi.json()['shortenedUrl']
	return render_template('slviewcode.html',link=link)#redirect (url_for('viewpr',idp=post.id_p))

@app.route("/viewcodext/<string:info>",methods=['GET', 'POST']) #dùng để nhúng vào dethi.pro
def viewcodext(info=None):
	data=[]
	dethi = Dethi.query.filter_by(id=int(info)).first()
	if dethi is None: return "dethi None"
	for idpost in dethi.post_id.all():
		post = Post.query.filter_by(id=idpost.id_post).first()
		lang = ['cpp','py','pas']
		for ext in lang:
			code = Submitcode.query.filter(Submitcode.ext==ext,Submitcode.fulltest==1,Submitcode.problem==post.id).order_by(Submitcode.id.desc()).first()
			if code is None: continue
			title = "["+app.config['LNAME'][ext] + "] " + post.id_name
			tmp={"id":code.id,"code":code.code,"ext":app.config['L2L_'][code.ext],"title":title,"numrow":len(code.code.split("\n"))}
			data.append(tmp)
	return render_template('viewcodext.html',data=data)

@app.route("/viewcode/<string:info>",methods=['GET', 'POST'])
@app.route("/viewcode/",methods=['GET', 'POST'])
@login_required
def viewcode(info=None):
	
	if info is None: return "Có lỗi"
	code = Submitcode.query.filter_by(id=int(info)).first()
	user = User.query.filter_by(username=code.user).first()
	log=str(code.log).replace("\n","<br>")
	post=Post.query.filter_by(id=code.problem).first()
	checkcode = (current_user.username==code.user or fhp_permit(["superadmin","admin"]))
	checkcode = (checkcode or Giaovienhs.query.filter(Giaovienhs.gv_id==current_user.id,Giaovienhs.hs_id==user.id).first() is not None)
	if checkcode==False:
		return render_template('error.html',messeg="Không được xem chương trình của người khác.",data=None)
	if code is None: return render_template('error.html',messeg="Có lỗi.",data=None)
	ext=app.config['L2L_'][code.ext]
	session['meta']['title']="Code: "+post.id_p+" hpcode.edu.vn"
	width,MAXX=12,0
	for xline in code.code.split("\n"): MAXX=max(MAXX,len(xline)+xline.count('\t'))
	width=max(MAXX//10+(MAXX%10>0)+1,3)
	data={"code":code.code,"user":code.user,"pro":post.id_p,"ext":ext,"namepr":post.id_name,"width":width,'log':log}

	return render_template('viewcode.html',data=data)
	# except Exception as e: writelogerr(e)
	# return render_template('error.html',messeg="Có lỗi")

@app.route("/viewcodeex/<string:info>",methods=['GET', 'POST']) #Xem chương trình của user nộp khi chạy với ví dụ
@app.route("/viewcodeex/",methods=['GET', 'POST'])
@login_required
def viewcodeex(info=None):
	if fhp_permit(["superadmin","admin"])==0: 
		return render_template('error.html',messeg="Bạn không có quyền xem chương trình ví dụ",data=None)
	if info is None: return "Có lỗi"

	code = Runexam.query.filter_by(id=int(info)).first()
	post=Post.query.filter_by(id=code.idp).first()
	
	if code is None: return render_template('error.html',messeg="Không có chương trình.",data=None)
	ext=app.config['L2L_'][code.ext]
	session['meta']['title']="Code: "+post.id_p+" hpcode.edu.vn"
	width,MAXX=12,0
	for xline in code.code.split("\n"): MAXX=max(MAXX,len(xline)+xline.count('\t'))
	width=max(MAXX//10+(MAXX%10>0)+1,3)
	data={"code":code.code,"user":code.user,"pro":post.id_p,"ext":ext,"namepr":post.id_name,"width":width}
	
	return render_template('viewcodeex.html',data=data)

@app.route("/viewsolution/",methods=['GET', 'POST'])
def viewsolution(): #xem một chương trình ngẫu nhiên đã làm đúng của một bài tập
	import time

	tbegin = time.time()
	session['meta']['title']="Xem chương trình - hpcode.edu.vn"
	fname = "app/static/data/post.txt"
	if not os.path.isfile(fname):
		f = open(fname,"w",encoding="utf-8")
		for post in Post.query.all(): f.write(post.id_p+"@"+post.id_name+"\n")
		f.close()
	f = open(fname,"r",encoding="utf-8")
	listidp = [ datax.split("@") for datax in f.read().split("\n")[:-1]]
	f.close()

	listidp=sorted(listidp,key=lambda x:x[0])
	if request.method == 'POST':
		idp  = request.form['idp']
		lang = request.form['lang']
		if idp =="" or lang =="": 
			status="Chọn bài tập và Ngôn ngữ lập trình để xem chương trình"
			return render_template('viewsolution.html',data={},listidp=listidp,status=status)
		post=Post.query.filter_by(id_p=idp).first()
		data={"namepr":post.id_name,"pro":post.id_p,'lang':{'py':"Python",'cpp':"C++",'pas':"Pascal"},"num":{'py':0,'cpp':0,'pas':0,'sb3':0}}
		getAC=None
		if current_user.is_authenticated:
			getAC=Submitcode.query.filter(Submitcode.user==current_user.username,Submitcode.problem==post.id,Submitcode.fulltest==True).first()
			if fhp_permit(["freecode"])==1: getAC = 1 #Dành cho đối tượng được xem code
		if len(checkPinC(post))>0 and getAC is None:
			status="Bài tập "+post.id_p+" đang trong kỳ thi. Bạn cần làm đúng trước khi tham khảo chương trình người khác"
			return render_template('viewsolution.html',data=data,listidp=listidp,status=status)
		
		x=[sb for sb in Submitcode.query.filter(Submitcode.problem==post.id,Submitcode.fulltest==1).all()]
		for tmp in x: data["num"][tmp.ext]+=1

		if data["num"][lang]==0: 
			status="Bài tập "+post.id_p+" chưa có chương trình *."+lang
			return render_template('viewsolution.html',data=data,listidp=listidp,status=status)
		else:
			while 1:
				sbx=x[random.randint(0,len(x)-1)]
				if sbx.ext==lang: break
			session['meta']['title']="Code: "+post.id_p+" hpcode.edu.vn"
			MAXX=0
			for xline in sbx.code.split("\n"): MAXX=max(MAXX,len(xline)+xline.count('\t'))
			data["code"]=sbx.code
			data["user"]=sbx.user
			data["width"]=max(MAXX//10+(MAXX%10>0)+1,3)
			data['log']=str(sbx.log).replace("\n","<br>")
			data["ext"]=app.config['L2L_'][sbx.ext]
			print(data["ext"])
			return render_template('viewsolution.html',data=data,listidp=listidp)
	#print("viewSolution",time.time()-tbegin)
	return render_template('viewsolution.html',data={},listidp=listidp)

@app.route("/taidethi/",methods=['GET', 'POST'])
@login_required
def taidethi():
	if current_user.giaovien!=1: return render_template('error.html',messeg="Bạn không thuộc đối tượng tải đề <hr>",data=None)
	#return render_template('error.html',messeg="Chức năng này tạm thời ngừng hoạt động. Mong bạn thông cảm và quay lại sau",data=None)
	idx = request.args.get('idde')
	
	fname = "app/static/chambai/tmp/dethi_"+str(idx)+".txt"
	f=open(fname,"w",encoding="utf-8")
	f.close()
	allowd = int(request.args.get('allow'))
	namekythi = request.args.get('kythi')
	session['meta']['title']="hpcode.edu.vn "+remove_tags(namekythi)
	mark = 0
	sode =Dethi.query.filter(Dethi.username==current_user.username,Dethi.check==1).count() #Số đề đã góp
	soded=current_user.dethi.count() # Số đề đã tải
	check = Dethi.query.filter(Dethi.username==current_user.username,Dethi.check==1, Dethi.id==idx).first() #Kiểm tra đề thi là của người tải đóng góp hay không?
	checkdatai = Dethiuser.query.filter(Dethiuser.id_user==current_user.id,Dethiuser.id_dethi==idx).first() #Kiểm tra user đã tải đề thi hay chưa
	
	if sode*20-soded<=0 and check is None and checkdatai is None: #Không có số đề miễn phí và đề thi không phải user góp và chưa tải
		if allowd==0: return render_template('taidethi.html',stt=1,idde=idx,namekythi=namekythi)
		else:
			#Không đủ điểm để tải
			if current_user.ndow<500: return render_template('taidethi.html',stt=2,namekythi=namekythi)
			mark = 500
	px = multiprocessing.Process(target=taidethi_function, args=(idx,current_user.username,))
	px.start()
	free = 1 if mark == 0 else 2 #free = 1 Đề tải miễn phí; free = 2 Đề thi được tải bằng điểm
	#User chưa tải đề thi thì ghi nhận đã tải
	if checkdatai is None: 
		db.session.add(Dethiuser(id_dethi=idx,id_user=current_user.id,free=free))
		#tăng điểm cho tác giả của đề thi
		username = Dethi.query.filter_by(id=idx).first().username
		user = User.query.filter_by(username=username).first()
		if current_user.username != username: user.ndow+=50
	current_user.ndow -=mark
	db.session.commit()
	
	sode =Dethi.query.filter(Dethi.username==current_user.username,Dethi.check==1).count() #Số đề đã góp
	soded=current_user.dethi.filter(free!=2).count() # Số đề đã tải miễn phí
	print("Số đề còn lại",sode*20-soded)
	return render_template('taidethi.html',sode_conlai=sode*20-soded,idde=idx,stt=3,namekythi=namekythi)

	# dethi=[ d.id for d in Dethi.query.filter(Dethi.username!=current_user.username,Dethi.check==1).all()] #Tất cả đề thi đã duyệt
	# detai=[ d.id_dethi for d in current_user.dethi.all()] #Tất cả đề thi đã tải
	# for x in detai: dethi.remove(x)
	# if len(dethi)==0: return render_template('error.html',messeg="Bạn đã tải hết đề thi mà chúng tôi có.",data=None)
	# idx=dethi[random.randint(0,len(dethi)-1)]
	
	# db.session.add(Dethiuser(id_dethi=idx,id_user=current_user.id))
	# db.session.commit()
	# return render_template('download.html',link=link)
	return "done"
def get_dir_size(path='.'):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total
def getfile_dethi(file,filename):
		file.save(filename)
		f=open(filename,"rb")
		datax = f.read()
		f.close()
		return datax
@app.route("/gopde/",methods=['GET', 'POST'])
@login_required
def gopde():
	if fhp_permit(["superadmin"])==0: return render_template('error.html',messeg="Chức năng này đang bị hạn chế!",data=None)
	if current_user.ndow<500:
		return render_template('error.html',messeg="Bạn cần đạt tối thiểu 500 điểm để Góp đề",data=None)
	dethi = Dethi.query.filter(Dethi.username==current_user.username, Dethi.check==0).count()
	if dethi>=5 and fhp_permit(["superadmin"])==0:
		return render_template('error.html',messeg="Bạn còn "+str(dethi)+" đề thi chưa được duyệt",data=None)
	ffolder = "app/static/data"
	filesize = get_dir_size(ffolder)
	if filesize//1024//1024>1024: 
		st = "Đang có nhiều đề thi chưa được duyệt. Mong bạn thông cảm và quay lại sau!"
		return render_template('error.html',messeg=st,data=None)
	st="Chức năng đang thử nghiệm.<br> Vui lòng chờ đến 02/8/2022"
	if current_user.username!="haiphong" and fhp_permit(["superadmin"])==0 and datetime.now()<datetime.strptime('01/08/2022 23:59:00', '%d/%m/%Y %H:%M:%S'): return render_template('error.html',messeg=st,data=None)
	status=None
	cv=app.config['CV']
	datagopde = [["dedocx","Đề thi (.docx)","required",".docx"],
                 ["depdf","Đề thi (*.pdf)","required",".pdf"],
                 ["soldocx","Hướng dẫn (*.docx)","",".docx"],
                 ["solpdf","Hướng dẫn (*.pdf)","",".pdf"]]
	if fhp_permit(["admin"]): datagopde[0][2]=datagopde[1][2]=""

	if request.method == 'POST':
		if request.form.get('checker') is None: return render_template('error.html',messeg="Bạn không đồng ý với quy định",data=None)
		#link = request.form['link']
		new_de=Dethi(kythi = request.form['kythi'])
		db.session.add(new_de)
		
		new_de.year2 = request.form['year']
		new_de.tinh = request.form['tinh']
		# new_de.link=link
		new_de.username=current_user.username
		new_de.note=request.form['note']
		new_de.makythi=cv[request.form['kythi']]
		
		fname =no_accent_vietnamese(new_de.tinh+"_"+new_de.makythi+"_"+new_de.year2+"_"+current_user.username+"_"+str(random.randint(1,1000)))
		new_de.fname = fname
		dedocx = request.files['dedocx']
		if dedocx.filename !='': new_de.dedocx = getfile_dethi(dedocx,os.path.join(ffolder,fname+".docx"))
		
		depdf = request.files['depdf']
		if depdf.filename !='': new_de.depdf = getfile_dethi(depdf,os.path.join(ffolder,fname+".pdf"))
		
		soldocx = request.files['soldocx']
		
		if soldocx.filename !='': new_de.sol = getfile_dethi(soldocx,os.path.join(ffolder,fname+"_sol.docx")) 
		
		solpdf = request.files['solpdf']
		if solpdf.filename!='': new_de.solpdf = getfile_dethi(solpdf,os.path.join(ffolder,fname+"_sol.pdf"))
		request.files.getlist('testcase')[0].save(os.path.join(ffolder,fname+".zip"))
		db.session.commit()
		status="Cảm ơn "+current_user.fullname+" đã góp đề"

	f=open('app/static/tinhthanh.txt',"r",encoding='utf-8'); tinh=f.read().split('\n'); f.close()

	dethi= Dethi.query.filter_by(username=current_user.username).all()
	post={}
	for d in dethi:
		post[d.id]=[]
		for idpost in d.post_id.all(): #Duyệt các id trong Dethi_post
			p=Post.query.filter_by(id=idpost.id_post).first()
			post[d.id].append(p.id_p)

	sode =Dethi.query.filter(Dethi.username==current_user.username,Dethi.check==1).count() #Số đề đã góp
	soded=current_user.dethi.count() # Số đề đã tải		

	denhan=[]
	for d in current_user.dethi.all():
		dt=Dethi.query.filter_by(id=d.id_dethi).first()
		denhan.append({"ngaytai":d.ngaytai,"kythi":dt.kythi,"year":dt.year,"username":dt.username,"tinh":dt.tinh})
	denhan=sorted(denhan, key=lambda d: d['ngaytai'], reverse=True)
	return render_template('gopde.html',year=datetime.today().year-5, tinh=tinh,status=status, dethi=dethi,post=post,slde=sode*20-soded,denhan=denhan,datagopde=datagopde)

@app.route("/addde/",methods=['GET', 'POST'])
@login_required
def addde():
	cv=app.config['CV']
	if fhp_permit(["superadmin"])==0: return render_template('error.html',messeg="Bạn không có quyền Thêm đề",data=None)

	idx = request.args.get('idx')
	if idx is None: idx=Dethi.query.filter(Dethi.check==1).order_by(Dethi.id.desc()).first().id
	dethi = Dethi.query.filter_by(id=idx).first()
	if dethi.notetitle is None: dethi.notetitle = ""
	if request.method == 'POST':
		files = request.files.getlist('file[]')
		dethi.username= request.form['nguoigop'] 
		dethi.kythi= request.form['tenkythi'] 
		dethi.tinh= request.form['tinh']
		dethi.year2= request.form['year']
		dethi.makythi = cv[request.form['tenkythi']]
		dethi.notetitle= request.form['notetitle']

		nameT = "Đề thi "+dethi.kythi+" tỉnh "+dethi.tinh+" năm học "+dethi.year2
		
		nameT = "<a href=\""+ app.config["DOMAIN"] +"xemde/?idde="+str(dethi.id)+"\" target=\"blank\">"+nameT+"</a>"
	
		for file in files:
			if "." not in file.filename: continue
			filename = secure_filename(file.filename).lower()
			extfile = filename.split(".")[-1]
			if extfile not in ["docx","pdf"]: continue
			linkt=os.path.join("app/static/chambai/tmp",filename)
			file.save(linkt)
			f=open(linkt,"rb")
			
			if "_sol.docx" in filename: dethi.sol=f.read()
			if "_sol.pdf" in filename: dethi.solpdf=f.read()
			if "_sol" not in filename and extfile == "docx": dethi.dedocx=f.read()
			if "_sol" not in filename and extfile =="pdf": dethi.depdf=f.read()
			f.close()
		db.session.commit()
		num = int(request.form['num'])
		ct = Tags.query.filter_by(tagname = dethi.makythi).first()#Kỳ thi

		for i in range(1,num+1):
			idp = int(request.form['idp'+str(i)]) #Lấy mã bài tập
			stt = int(request.form['stt'+str(i)]) #Lấy số thứ tự bài tập
			dethipost=Dethi_post.query.filter(Dethi_post.id_dethi==idx,Dethi_post.id_post==idp).first()
			
			if  dethipost is not None:
				dethipost.stt=stt
				if stt==0: #Xoá bài tập trong đề thi
					if ct is not None and dethi.makythi in ['ts10','hsga','hsgb','thcs']: #Xoá bài tập trong kỳ thi	
						tp = Tag_post.query.filter(Tag_post.id_tag==ct.id,Tag_post.id_post==idp).first()
						if tp is not None : db.session.delete(tp)
					db.session.delete(dethipost)
					continue
				post = Post.query.filter_by(id=idp).first()
				post.source=nameT
			elif stt>0:
				db.session.add(Dethi_post(id_dethi=idx,id_post=idp,stt=stt))#Thêm bài vào Đề thi
				post = Post.query.filter_by(id=idp).first()
				post.source=nameT
				tp = None
				if ct is not None: tp = Tag_post.query.filter(Tag_post.id_tag==ct.id,Tag_post.id_post==idp).first()
				if tp is None and dethi.makythi in ['ts10','hsga','hsgb','thcs']: db.session.add(Tag_post(id_tag=ct.id,id_post=idp,maxsub=10)) #Thêm bài vào Kỳ thi

		db.session.commit()

	dethi=Dethi.query.filter_by(id=int(idx)).first()	

	post=[]#Tất cả các bài tập trong đề thi
	for idpost in dethi.post_id.all(): #Duyệt các id trong Dethi_post
		p=Post.query.filter_by(id=idpost.id_post).first()
		if p is None: continue
		post.append({'stt':idpost.stt,'idp':p.id_p,'idname':p.id_name,'id':p.id})
	for i in range(max(1,6-len(dethi.post_id.all()))):
		post.append({'stt':0,'idp':"",'idname':"Chọn bài tập thêm vào kỳ thi",'id':0})
	
	data=Dethi.query.filter(Dethi.check==1).order_by(Dethi.id.desc()).all()
	allpost= Post.query.order_by(Post.id.desc()).all()

	f=open('app/static/tinhthanh.txt',"r",encoding='utf-8'); tinh=f.read().split('\n'); f.close()
	luser = [user.username for user in User.query.order_by(User.username.asc()).all()]
	return render_template('addde.html',info=dethi,post=sorted(post, key=lambda d: d['stt']),data=data,allpost=allpost,tinh=tinh,luser=luser)

@app.route("/duyetde/",methods=['GET', 'POST'])
@login_required
def duyetde():
	session['meta']['title']="Duyệt đề - hpcode.edu.vn"
	if fhp_permit(["superadmin"])==0:
		return render_template('error.html',messeg="Bạn không có quyền Duyệt đề",data=None)
	if request.method == 'POST':
		check= (request.form['submit']=="Đồng ý")
		idx = int(request.form['idx'])
		dethi=Dethi.query.filter_by(id=idx).first()
		if dethi is None: render_template('error.html',messeg="không tìm thấy bản ghi",data=None)
		dethi.cmt=request.form['cmt']
		dethi.ngayduyet=datetime.now()
		dethi.tinh= request.form['tinh']
		dethi.kythi = request.form['kythi']
		dethi.year2 = request.form['year']
		if check == False: dethi.check=2
		if check == True: 
			dethi.check=1; #os.remove("app/static/dethi/danhsach.txt")

		db.session.commit()
	g=Dethi.query.filter_by(check=0).order_by(Dethi.id.asc()).first()
	idde = request.args.get('idde')
	if idde is not None: g=Dethi.query.filter(Dethi.check==0,Dethi.id==idde).first()
	
	if g is None: return render_template('error.html',messeg="Đã duyệt hết bản ghi",data=None)

	data={'id':g.id,'username':g.username,'ngaygop':g.ngaygop,'kythi':g.kythi,'tinh':g.tinh,'link':[],'year':g.year2,'count':0,'link':''}
	#if g.link != "": data['link'].append(g.link)
	data['ngaygop']=g.ngaygop
	data['note']=g.note
	data['fname'] =[]
	
	for x in ['.docx','.pdf','_sol.docx','_sol.pdf','.zip']:
		if g.fname is not None and os.path.isfile("app/static/data/"+g.fname+x): data['fname'].append("static/data/"+g.fname+x)
	data['count']=Dethi.query.filter_by(check=0).order_by(Dethi.id.asc()).count()
	tmp = urlparse(request.url)
	data['link']=tmp.scheme +"://"+tmp.netloc + "/"

	return render_template('duyetde.html',data=data)

@app.route("/xemde/",methods=['GET', 'POST'])
def xemde():
	#if fhp_permit(['xemde'])==0: return render_template('error.html',messeg="Bạn không thuộc đối tượng XEM ĐỀ THI <hr>",data=None)
	#if current_user.is_anonymous: return render_template('error.html',messeg="Bạn cần phải đăng nhập để XEM ĐỀ THI <hr>",data=None)
	idde = request.args.get('idde')
	dethi=Dethi.query.filter_by(id=idde).first()
	if dethi is None: return render_template('error.html',messeg="Kỳ thi không tồn tại",data=None)
	year2 = str(dethi.year2)
	if dethi.luotxem is None: dethi.luotxem = 0
	dethi.luotxem +=1
	db.session.commit()
	if dethi.kythi == "Olympic 30/4": year2 = str(dethi.year2).split("-")[1]
	namekythi = "Đề thi "+dethi.kythi+" tỉnh "+dethi.tinh+" năm "+year2
	if dethi.notetitle: namekythi=namekythi+" "+dethi.notetitle
	fnkythi = "["+str(dethi.id)+"]["+dethi.kythi+"]["+dethi.tinh+"]["+year2+"]"
	check={"de":dethi.dedocx,"sol":dethi.sol,"daduyet":dethi.check}
	session['meta']['title']=namekythi
	session['meta']['des']=namekythi
	if dethi.depdf is None: return render_template('error.html',messeg="Kỳ thi <b>"+namekythi+"</b> chưa có đề",data=None)
	
	fn=os.path.join("app/static/hppdf/",fnkythi.replace("/",".")+".pdf")
	if not os.path.isfile(fn):
		f=open(fn,"wb")
		f.write(dethi.depdf)
		f.close()
	put_watermark(fn, fn, "app/static/WM_hpcode.pdf")
	tmp = urlparse(request.url)
	urlx = tmp.scheme +"://"+tmp.netloc + "/"
	fn = urlx + fn[4:]

	post=[]
	for idpost in dethi.post_id.all(): #Duyệt các id trong Dethi_post
		p=Post.query.filter_by(id=idpost.id_post).first()
		post.append(p.id_p)

	return render_template('xemdethi.html',idde=dethi.id,namekythi=namekythi,tacgia=dethi.username,post=post,check=check,fn=fn)
@app.route("/dethi/",methods=['GET', 'POST'])
def dethi():
	namekythi="Đề thi HSG môn Tin học"
	data={"kythi":["Tất cả"],"tinh":["Tất cả"],"namhoc":["Tất cả"]}
	tmpde = Dethi.query.filter(Dethi.check<2).order_by(Dethi.year2.desc())
		
	if request.method == 'POST':
		namekythi = "Đề thi "
		if request.form['kythi']!="Tất cả":
			data["kythi"]=[request.form['kythi'],"Tất cả"]
			namekythi +=  "<b>"+request.form['kythi']+"</b>"
			tmpde = tmpde.filter_by(kythi=request.form['kythi'])
				
		if request.form['tinh']!="Tất cả":
			data["tinh"]=[request.form['tinh'],"Tất cả"]
			if request.form['tinh'] in ["Hải Phòng","Đà Nẵng","Cần Thơ","Hồ Chí Minh","Hà Nội"]:
				namekythi +=  "  TP <b>"+request.form['tinh']+"</b>"
			else:
				namekythi +=  "  tỉnh <b>"+request.form['tinh']+"</b>"
			tmpde = tmpde.filter_by(tinh=request.form['tinh'])
		if request.form['namhoc']!="Tất cả":
			data["namhoc"]=[request.form['namhoc'],"Tất cả"]
			namekythi +=  " năm học <b>"+request.form['namhoc']+"</b>"
			tmpde = tmpde.filter_by(year2=request.form['namhoc'])
	dethi=[]
	for d in tmpde.all():
		if d.kythi=="HSG Chọn đội tuyển": d.kythi="HSG Chọn Đội tuyển"
		if d.notetitle is None: d.notetitle=""
		#ctai = Dethiuser.query.filter_by(id_dethi=d.id).count()
		year2 = d.year2
		if d.kythi == "Olympic 30/4": year2 = str(d.year2).split("-")[1]
		luotxem = 0 if d.luotxem is None else d.luotxem
		dtmp = {"kythi":d.kythi,"tinh":d.tinh,"namhoc":year2,"nguoigop":d.username,"idde":d.id,"stt":d.check,"luotxem":luotxem,"notetitle":d.notetitle}
		dethi.append(dtmp)
	db.session.commit()
	data["kythi"].extend(["Tuyển sinh 10","HSG THCS","HSG Chọn Đội tuyển","HSG THPT","Olympic 30/4","Duyên Hải Bắc Bộ","Tin học trẻ","Khác..."])
	f=open('app/static/tinhthanh.txt',"r",encoding='utf-8'); data["tinh"].extend(f.read().split('\n')); f.close()
	for i in range(2010,datetime.now().year+1): data["namhoc"].append(str(i)+"-"+str(i+1))
	session['meta']['title']=remove_tags(namekythi)
	session['meta']['des']=remove_tags(namekythi)

	return render_template('dethi.html', dethi=dethi,namekythi=namekythi,data=data)

@app.route("/downloadde/",methods=['GET', 'POST'])
@login_required
def downloadde():
	idde = int(request.args.get('idde'))
	tag = int(request.args.get('tag')) #1 là đề #2 là Solution
	dethi=Dethi.query.filter_by(id=idde).first()
	if dethi is None: return render_template('error.html',messeg="Đề thi không tồn tại",data=None)
	title="hpcode.edu.vn_"+str(dethi.year2)+"_"+str(dethi.tinh)+"_"+str(dethi.kythi)
	session['meta']['title']=title
	mark=100 if tag==1 else 20
	if fhp_permit(['superadmin'])==1: mark=0
	fn=""
	if tag==1 and current_user.ndow>=mark and dethi.dedocx is not None:
		title=title+"_dethi.docx"
		fn=os.path.join("app/static/chambai/tmp/",title)
		data=dethi.dedocx
	elif current_user.ndow>=mark and dethi.sol is not None:
		title=title+"_solution.docx"
		fn=os.path.join("app/static/chambai/tmp/",title)
		data=dethi.sol
	if current_user.ndow<mark: return render_template('error.html',messeg="Bạn không đủ điểm để tải",data=None)
	current_user.ndow=current_user.ndow-mark
	db.session.commit()
	f=open(fn,"wb")
	f.write(data)
	f.close()
	tmp = urlparse(request.url)
	return render_template('download.html',link=tmp.scheme +"://"+tmp.netloc+"/"+fn[4:])

@app.route("/getpdf/",methods=['GET', 'POST'])
@login_required
def getpdf():
	idp = request.args.get('idp')
	post=Post.query.filter_by(id_p=idp).first()
	session['meta']['title']="Pdf: "+post.id_p+" hpcode.edu.vn"
	if post is None: return render_template('error.html',messeg="Bài tập không tồn tại",data=None)
	if post.pdf is None: return render_template('error.html',messeg="Bài tập chưa có tệp PDF",data=None)
	fn=os.path.join("app/static/chambai/tmp",post.id_p+".pdf")
	f=open(fn,"wb")
	f.write(post.pdf)
	f.close()
	return render_template('download.html',link="../static/chambai/tmp/"+idp+".pdf")
@app.route("/setdef/",methods=['GET', 'POST'])
@login_required
def setdef():
	if request.method == 'POST':
		current_user.langdf=request.form['langtmp']
		#current_user.layout=int(request.form['layout'])
		db.session.commit()
	return redirect(url_for('index'))
#@app.route("/viewpr/<string:idp>",methods=['GET', 'POST'])
@app.route("/viewpr/",methods=['GET', 'POST'])
def viewpr():
	idp = request.args.get('idp')
	if idp is None: return render_template('error.html',messeg="Chưa chọn bài tập",data=None)
	#if current_user.is_authenticated: return redirect (url_for('viewctpr',idp=idp))
	p =  Post.query.filter_by(id_p=idp).first()
	if p is None: return render_template('error.html',messeg="Không tìm thấy bài tập")
	if current_user.is_authenticated and current_user.khoatk!=1:
		return redirect (url_for('viewctpr',idp=idp))
	session['meta']['title']=p.id_name+" - hpcode.edu.vn"
	session['meta']['des']= remove_tags(p.body[:min(len(p.body),500)])
	problem=getProblem(p,[])
	return render_template('viewpr.html',problem=problem)
@app.route("/runcodetmp/",methods=['GET', 'POST'])
#@login_required
def runcodetmp():
	username = current_user.username
	if request.method == 'POST': 
		idp = request.form['idp']
		p=Post.query.filter(Post.id_p == idp).first()
		session['meta']['title']=p.id_name+" - hpcode.edu.vn"
		session['meta']['des']=remove_tags(p.body[:min(len(p.body),500)])
		if str(p.source)!="None": 
			session['meta']['des']=p.source+" - "+remove_tags(p.body[:min(len(p.body),150)])
		ccode = request.form['ccode']
		if check_VN(ccode.lower())==1: return
		if "import os" in ccode or "subprocess" in ccode: return
		if "system" in ccode.lower(): return
		if "cmd.exe" in ccode: return
		extcode=request.form['lang']#Ví dụ c_cpp
		ext = app.config['L2L'][extcode]#=>Chuyển về cpp
		
		exam=Runexam(idp=p.id,user=username,inp=request.form['testin'],ext=ext,code=ccode,graded=0)
		db.session.add(exam)
		db.session.commit()
		
		filelogs = str(exam.id)+'.'+ext+'.log'
		tmpww = Submitcode.query.filter_by(graded=0).count()
		tmpww = "Đang chờ..." if tmpww==1 else "Đang chờ ..."+str(tmpww-1)+" bài khác"
		createlog("app/static/chambai/tmp/"+filelogs,tmpww,0)
		return jsonify({'idlog' : filelogs})
	return render_template('error.html',messeg="Xin chào "+username+"! Bạn đang làm gì ở đây?")

@app.route("/runcode/",methods=['GET', 'POST'])
@login_required
def runcode():
	username = current_user.username
	
	filelogs = username+"_check_hack.log"
	if request.method == 'POST': 
		idp = request.form['idp']
		p=Post.query.filter(Post.id_p == idp).first()
		session['meta']['title']=p.id_name+" - hpcode.edu.vn"
		session['meta']['des']=remove_tags(p.body[:min(len(p.body),150)])
		
		slsub= Submitcode.query.filter(Submitcode.user==username,Submitcode.problem==p.id).count()
		listc=[]
		for tp in checkPinC(p): #Xét từng Contest có sự tham gia của bài tập
			if checkDoituong(tp)==1: #Nếu user thuộc đối tượng tham gia
				listc.append(tp)
		maxsub=solannpbaiconlai()
		
		ischeck=None
		if str(p.source)!="None": session['meta']['des']=p.source+" - "+remove_tags(p.body[:min(len(p.body),150)])
		ccode = request.form['ccode']
		if check_VN(ccode.lower())==1: ischeck = "Không được dùng kí tự tiếng Việt"
		if " os" in ccode.lower() or "subprocess" in ccode.lower(): ischeck = "Bài nộp bị từ chối 1"
		if "system" in ccode.lower(): ischeck = "Bài nộp bị từ chối 2"
		if "cmd.exe" in ccode.lower(): ischeck = "Bài nộp bị từ chối 3"
		if contains_system_command(ccode): 
			print(username,"nộp bài có lệnh hệ thống")
			f=open(username+".txt","w")
			f.write(str(ccode))
			f.close()
			ischeck = "Bài nộp bị từ chối 4"
		if ccode=="": ischeck = "Bài nộp không có nội dung"
		if ischeck is not None:
			ischeck+="<br>=====xong====="
			createlog("app/static/chambai/tmp/"+filelogs,ischeck,0)
			return jsonify({'idlog' : filelogs,"slsub":slsub,"maxsub":maxsub})
		extcode=request.form['lang']#Ví dụ c_cpp
		ext = app.config['L2L'][extcode]#=>Chuyển về cpp
		
		sb=Runexam(idp=p.id,user=username,inp=request.form['testin'],ext=ext,code=ccode,graded=0)
		db.session.add(sb)
		db.session.commit()

		filelogs = str(sb.id)+'.'+ext+'.log'
		tmpww = Submitcode.query.filter_by(graded=0).count()
		tmpww = "Đang chờ..." if tmpww==0 else "Đang chờ ..."+str(tmpww-1)+" bài khác"
		createlog("app/static/chambai/tmp/"+filelogs,tmpww,0)
		process = multiprocessing.Process(target=jundle)
		process.start()
		return jsonify({'idlog' : filelogs,"slsub":slsub,"maxsub":maxsub})
	return render_template('error.html',messeg="Xin chào "+username+"! Bạn đang làm gì ở đây?")

@app.route("/submitcode/",methods=['GET', 'POST'])
#@login_required
def submitcode():
	username = current_user.username
	sbcount = Submitcode.query.filter(Submitcode.user==username,Submitcode.timesb>=datetime.now() - timedelta(seconds=60*3)).count()
	filelogs = username+"_check_hack.log"
	if request.method == 'POST': 
		idp = request.form['idp']
		p=Post.query.filter(Post.id_p == idp).first()
		session['meta']['title']=p.id_name+" - hpcode.edu.vn"
		pbody = p.body if p.body is not None else ""
		session['meta']['des']=remove_tags(pbody[:min(len(pbody),150)])
		
		slsub= Submitcode.query.filter(Submitcode.user==username,Submitcode.problem==p.id).count()
		listc=[]
		for tp in checkPinC(p): #Xét từng Contest có sự tham gia của bài tập
			if checkDoituong(tp)==1: #Nếu user thuộc đối tượng tham gia
				listc.append(tp)
		maxsub=solannpbaiconlai()
		
		if(slsub+1>maxsub): ischeck="Lượt nộp bài đã hết"
		if str(p.source)!="None": session['meta']['des']=p.source+" - "+remove_tags(pbody[:min(len(pbody),150)])
		extcode=request.form['lang']#Ví dụ c_cpp
		ext = app.config['L2L'][extcode]#=>Chuyển về cpp
		
		if ext=="sb3": 
			file = request.files['filesb3']
			print(file.filename.split(".")[-1])
			if file.filename.split(".")[-1]!='sb3': 
				createlog("app/static/chambai/tmp/"+filelogs,"Không đúng file Scratch",0)
				return jsonify({'idlog' : filelogs,"slsub":slsub,"maxsub":maxsub})
			timerun = datetime.now()

			fout = "["+str(timerun.timestamp())+"]["+username+"]["+p.id_p+"].sb3"
			file.save("C:/Alltest/Scratch/"+fout)
			sb=Submitcode(user=username,problem=p.id,ext=ext,code=fout,graded=0)
		else: 
			ischeck=None
			ccode = request.form['ccode']
			#if check_VN(ccode.lower())==1: ischeck = "Không được dùng kí tự tiếng Việt"
			if " os" in ccode or "subprocess" in ccode: ischeck = "Bài nộp bị từ chối"
			if "system" in ccode.lower(): ischeck = "Bài nộp bị từ chối"
			if "cmd.exe" in ccode.lower(): ischeck = "Bài nộp bị từ chối" 
			if contains_system_command(ccode): ischeck = "Bài nộp bị từ chối"
			if ccode=="": ischeck = "Bài nộp không có nội dung"
			if ischeck is not None:
				ischeck+="<br>=====xong====="
				createlog("app/static/chambai/tmp/"+filelogs,ischeck,0)
				return jsonify({'idlog' : filelogs,"slsub":slsub,"maxsub":maxsub})
			sb=Submitcode(user=username,problem=p.id,ext=ext,code=ccode,graded=0)
		db.session.add(sb)
		db.session.commit()
		filelogs = str(sb.id)+'.'+ext+'.log'
		if sbcount>=5:
			tmpww = "Xin chào <b>"+username+"</b>! <br> Bạn đã rất tích cực nộp bài trong 5 phút vừa qua! <h3 class='text-success'>Hãy nghỉ một chút trước khi tiếp tục</h3>=====xong====="
			createlog("app/static/chambai/tmp/"+filelogs,tmpww,0)
			db.session.delete(sb)
			db.session.commit()
			return jsonify({'idlog' : filelogs,"slsub":slsub+1,"maxsub":solannpbaiconlai()})
		tmpww = Submitcode.query.filter_by(graded=0).count()
		tmpww = "Đang chờ..." if tmpww==1 else "Đang chờ ..."+str(tmpww-1)+" bài khác"
		createlog("app/static/chambai/tmp/"+filelogs,tmpww,0)
		process = multiprocessing.Process(target=jundle) 
		process.start()
		#Tính số lượt tải/xem test còn lại
		countx= max(0,numview_testcase() - current_user.testid.filter(User_tests.time>datetime.now() - timedelta(days=1)).count())
		
		return jsonify({'idlog' : filelogs,"slsub":slsub+1,"maxsub":solannpbaiconlai(),"countx":str(countx)})
	return render_template('error.html',messeg="Xin chào "+username+"! Bạn đang làm gì ở đây?")

@app.route("/giaovien/",methods=['GET', 'POST'])
def giaovien():
	if current_user.is_anonymous or current_user.giaovien!=1: 
		return render_template('notegv.html')
	
	x1 = Giaovienhs.query.filter_by(gv_id=current_user.id).count()
	x2 = current_user.slhocsinh
	status = "<span class='text-success'>Bạn đã thêm <b>"+str(x1)+"/"+str(x2)+"</b> học sinh vào danh sách của mình</span>"
	data = []
	if request.method == 'POST':
		username = request.form['username']
		user = User.query.filter_by(username=username).first()
		if user is None:
			status = "<span class='text-danger'>Không tìm thấy học sinh có tên đăng nhập<b>"+username+"</b></span>"
		elif Giaovienhs.query.filter(Giaovienhs.gv_id==current_user.id,Giaovienhs.hs_id==user.id).first() is not None:
			status = status+"<span class='text-danger'><br><b>Học sinh đã có trong danh sách của bạn</b></span>"
		elif Giaovienhs.query.filter_by(hs_id=user.id).first() is not None:
			status = status+"<span class='text-danger'><br><b>Học sinh đã có trong danh sách của giáo viên khác</b></span>"
		elif Giaovienhs.query.filter_by(gv_id=user.id).first() is not None:
			status = status+"<span class='text-danger'><br><b>Không thể thêm Gáo viên làm học sinh của bạn</b></span>"
		elif x1<x2:
			db.session.add(Giaovienhs(gv_id=current_user.id,hs_id=user.id))
			user.thoihan = datetime.now() + timedelta(days=365) #Thời hạn 1 năm từ ngày được thêm vào học sinh
			user.khoatk=0 #Mở khóa tài khoản học sinh
			db.session.commit()
			status = status+"<span class='text-success'><br><b>Thêm học sinh thành công</b></span>"
	for gvhs in Giaovienhs.query.filter_by(gv_id=current_user.id).all():
		user = User.query.filter_by(id=gvhs.hs_id).first()
		if user is not None:
			tmp = {"username":user.username,"fullname":user.fullname,"AC1d":[],"WA1d":[],"AC1w":[],"WA1w":[],"thoihan":user.thoihan.strftime("%d/%m/%Y")}

			listsm=[sb for sb in Submitcode.query.filter(Submitcode.user==user.username,Submitcode.timesb>=datetime.now()+timedelta(days=-7)).all()]
			for sb in listsm:
				post = Post.query.filter_by(id=sb.problem).first()
				if post is None: continue
				if sb.fulltest==1 and sb.timesb>=datetime.now()+timedelta(days=-1) and post.id_p not in tmp["AC1d"]: tmp["AC1d"].append(post.id_p)
				if sb.fulltest==1 and post.id_p not in tmp["AC1w"]: tmp["AC1w"].append(post.id_p)			
			for sb in listsm:
				post = Post.query.filter_by(id=sb.problem).first()
				if post is None: continue
				if sb.fulltest!=1 and post.id_p not in tmp["AC1d"] and sb.timesb>=datetime.now()+timedelta(days=-1) and post.id_p not in tmp["WA1d"]: tmp["WA1d"].append(post.id_p)
				if sb.fulltest!=1 and post.id_p not in tmp["WA1w"] and post.id_p not in tmp["AC1w"]: tmp["WA1w"].append(post.id_p)

			data.append(tmp)
	return render_template('giaovien.html',data=data,status=status)
@app.route("/themisx/",methods=['GET', 'POST'])
def themisx():
	listnamecontest = ["baokhanh"]
	status = None
	fname = ""
	checknopbai = 0
	timeb =datetime.strptime("04/18/2025", '%m/%d/%Y')
	timee =datetime.strptime("04/25/2026", '%m/%d/%Y')
	

	lff = [ff.lower() for ff in os.listdir("app/static/themis/tests")]
	if request.method == 'POST' and current_user.is_authenticated:
		if datetime.now()<timeb: status = "<span class='text-danger'><b>Chưa đến giờ nộp bài!</b></span>"
		if datetime.now()>timee +timedelta(days=1): status = "<span class='text-danger'><b>Đã hết giờ nộp bài!</b></span>"
		f = request.files['file']
		if f.filename.split(".")[-1].lower() not in ["pas","cpp","py"]: status = "<span class='text-danger'><b>Định dạng tệp không đúng!</b></span>"
		if f.filename.split(".")[0].lower() not in lff: status = "<span class='text-danger'><b>tên tệp không đúng!</b></span>"
		if f.seek(0, os.SEEK_END)>1024*1024: status = "<span class='text-danger'><b>file quá lớn!</b></span>"
		if status is None:
			fname = str(int(datetime.today().timestamp()))+"["+current_user.username+"]["+f.filename.split(".")[0]+"]."+f.filename.split(".")[-1]
			fn = "app/static/themis/oj/"+fname
			f.seek(0, os.SEEK_SET)
			ccode = f.read().decode('utf-8').replace("freopen(","//freopen(")
			f.seek(0, os.SEEK_SET)
			f.save(fn)
			
			status = "<span class='text-success'><b>Nộp bài thành công</b></span>"
			checknopbai = 1
			
			idp = f.filename.split(".")[0].lower()
			ext = f.filename.split(".")[-1].lower()
			post = Post.query.filter_by(id_p=idp).first()
			db.session.commit()
			if post is None:
				user = User.query.filter_by(username = "admin").first()
				p = Post(id_p=idp,id_name="Chưa có tên",body="",user_id=user.id)
				db.session.add(p)
				db.session.commit()
			post = Post.query.filter_by(id_p=idp).first()
			sb=Submitcode(user=current_user.username,problem=post.id,ext=ext,code=ccode,graded=1)
			db.session.add(sb)
			db.session.commit()
			px = multiprocessing.Process(target=relpaceall, args=("app/static/themis/oj/logs/"+fname+".log",listnamecontest[0],sb.id))
			px.start()

	linkimg = 	"app/static/themis/dethi/dethi.jpg"
	linkdethi = "app/static/themis/dethi/dethi.pdf"
	linkimg_tmp = 	"app/static/themis/dethi/dethi_lhphongsdjkskdfusiuf12784736423.jpg"
	linkdethi_tmp = "app/static/themis/dethi/dethi_lhphongsdjkskdfusiuf12784736423.pdf"
	if not os.path.isfile(linkimg)  and timeb <= datetime.now()<= timee+timedelta(days=1):
		os.rename(linkimg_tmp,linkimg)
		os.rename(linkdethi_tmp,linkdethi)

	if not os.path.isfile(linkimg_tmp)  and not (timeb <= datetime.now()<= timee+timedelta(days=1)):
		os.rename(linkimg,linkimg_tmp)
		os.rename(linkdethi,linkdethi_tmp)

	checkdethi = None
	if os.path.isfile(linkdethi): 
		checkdethi = True
		linkimg = 	"../static/themis/dethi/dethi.jpg"
		linkdethi = "../static/themis/dethi/dethi.pdf"
	his = []
	fnroot = "app/static/themis/oj/logs/"
	if current_user.is_authenticated:
		for fn in os.listdir(fnroot):
			if "["+current_user.username+"]" not in fn: continue
			his.append(["../"+fnroot[3:],fn])
	his.sort(key=lambda x: x[1],reverse=True)
	ketqua = []
	fnroot = "app/static/themis/ketqua/"
	for fn in os.listdir(fnroot):
		ketqua.append(["../"+fnroot[3:],fn])
	data={'status':status,'linkdethi':linkdethi,'linkimg':linkimg,'his':his,'ketqua':ketqua,'checkdethi':checkdethi,'flog':fname+".log",'checknopbai':checknopbai}
	data['timeb']=timeb
	data['timee']=timee
	xtime = str(timeb).replace(" 00:00:00","")
	ytime = str(timee).replace(" 00:00:00","")
	data['timebx']=xtime[8:]+"/"+xtime[5:7]+"/"+xtime[:4]
	data['timeex']=ytime[8:]+"/"+ytime[5:7]+"/"+ytime[:4]
	print(data['timeex'])
	fct_root = "app/static/themis/oj/logs/"
	ccctimeb = time.time()
	contest = {}
	namepr = {}
	havetest = {}
	for fct in listnamecontest:#sorted(os.listdir(fct_root),reverse=True):
		fct_name = os.path.join(fct_root,fct) #Tên các Contest
		#if ".txt" in fct_name or '.log' in fct_name: continue
		contest[fct]={}
		for fn in os.listdir(fct_name):
			problem = fn.split("][")[1].split("]")[0].lower()
			if problem not in contest[fct]: 
				contest[fct][problem]=0
				post = Post.query.filter_by(id_p=problem).first()
				namepr[problem]=post.id_name if post is not None else "Chưa có tên"
				havetest[problem] = post.testcase.count() if post is not None else 0
			contest[fct][problem]+=1
	print("Contest",time.time()-ccctimeb)
	data['contest'] = contest
	data['namepr'] = namepr
	data['havetest'] = havetest

	return render_template('themis.html',data=data)
@app.route("/viewctpr/",methods=['GET', 'POST'])
#@login_required
def viewctpr():
	idp = request.args.get('idp')
	p=Post.query.filter(Post.id_p == idp).first()
	if p is None: return render_template('error.html',messeg="Không tìm thấy bài tập")
	if current_user.is_anonymous: return redirect (url_for('viewpr',idp=idp))
	if current_user.khoatk==1: return redirect (url_for('viewpr',idp=idp))
	username = current_user.username
	slsub= Submitcode.query.filter(Submitcode.user==username,Submitcode.problem==p.id).count()

	session['meta']['title']=p.id_name+" - hpcode.edu.vn"
	pbody = p.body if p.body is not None else ""
	session['meta']['des']= remove_tags(pbody[:min(len(pbody),150)]) 
	if str(p.source)!="None": session['meta']['des']=p.source+" - "+remove_tags(pbody[:min(len(pbody),150)])
	
	listc=[] #danh sách Contest có chứa bài tập mà User được phép tham gia
	for tp in checkPinC(p): #Xét từng Contest có sự tham gia của bài tập
		listc.append(tp)
	
	listc=sorted(listc, key=lambda x:x.ts, reverse=True)
	
	if len(listc)>0 and listc[0].ts>datetime.now(): 
		return render_template('error.html',messeg="Kỳ thi chưa bắt đầu")
	maxsub=solannpbaiconlai()
	extcode=current_user.langdf
	ccode=""
	if fhp_permit(["admin","superadmin"])==1:
		maxsub = 100
		ccode="#include <bits/stdc++.h>\nusing namespace std;\nint main()\n{\n    //Type your code here\n   return 0;\n}"
	
	problem=getProblem(p,listc)#Lấy thông tin của bài tập
	problem["user"]=username #Tên đăng nhập của người đang làm bài
	problem["tmpcode"]= ccode
	problem["ext"]=extcode
	problem["numsub"]={"slsub":slsub,"maxsub":maxsub}
	problem["alltestcase"]=[]
	
	for x in p.testcase:
		utest = User_tests.query.filter(User_tests.userid==current_user.id,User_tests.testid==x.id).order_by(User_tests.time.desc()).first()
		timex = utest.time.strftime("%H:%M:%S, %d/%m/%Y") if utest is not None else "./."
		problem["alltestcase"].append([x.id,timex])
	
	#if len(checkPinC(p))>0: problem["sol"]=None

	listsub=[] #Tất cả bài nộp cho bài p.id
	listsubuser=[] #bài nộp của user đang đăng nhập cho bài tập p.id
	lists=Submitcode.query.order_by(Submitcode.id.desc()).filter(Submitcode.problem==p.id)
	for i,s in enumerate(lists):
		user = User.query.filter_by(username=s.user).first()
		if user is None: continue
		tmp={"numtest":s.numtest,"alltest":p.testcase.count(),"user":s.user,"id_p":p.id_p,"ext":s.ext,
		     "time":(str(s.timesb)+'.').split(".")[0],"idp":p.id,"ids":s.id, "checkcode":0}
		if fhp_permit(["admin","superadmin"])==1: tmp["checkcode"] = 1
		if current_user.username==s.user: tmp["checkcode"] = 1
		if current_user.giaovien==1 and Giaovienhs.query.filter(Giaovienhs.hs_id==user.id, Giaovienhs.gv_id==current_user.id).first() is not None:
			tmp["checkcode"] = 1

		if len(listsub)<50: listsub.append(tmp)
		if s.user==username: listsubuser.append(tmp)
	#Tính số lượt tải/xem test còn lại
	countx= max(0,numview_testcase() - current_user.testid.filter(User_tests.time>datetime.now() - timedelta(days=1)).count())
	
	return render_template('viewctpr.html',countx=countx,problem=problem,listsub=listsub,listsubuser=listsubuser,checkads=1)
 
@app.route("/runexam/",methods=['GET', 'POST'])
def runexam():
	data={}
	data['ext']="c_cpp"
	data['ccode']=""
	username=current_user.username if current_user.is_authenticated else "anonymous" 
	data['username'] = username
	session['meta']['title']=data['username']+" - Runexam - hpcode.edu.vn"
	if request.method == 'POST':
		data['ccode'] = request.form['ccode']
		if data['ccode']=="": return render_template('error.html',messeg="Chưa có nội dung",data=None)
		if "import os" in data['ccode'].lower(): return render_template('error.html',messeg="Bài nộp của bạn bị từ chối",data=None)
		if "system" in data['ccode'].lower(): return render_template('error.html',messeg="Bài nộp của bạn bị từ chối",data=None)
		if "shutdown" in data['ccode'].lower(): return render_template('error.html',messeg="Bài nộp của bạn bị từ chối",data=None)
		if "cmd.exe" in data['ccode'].lower(): return render_template('error.html',messeg="Bài nộp của bạn bị từ chối",data=None)
		extcode=request.form['lang']#Ví dụ c_cpp
		data['ext'] = extcode
		ext= app.config['L2L'][extcode]#=>Chuyển về cpp
		
		exam=Runexam(idp=1,user=username,inp=request.form['testin'],ext=ext,code=data['ccode'])
		db.session.add(exam)
		db.session.commit()
		print("id",exam.id)
		data['filelogs']=str(exam.id)+"."+exam.ext+".log"
		process = multiprocessing.Process(target=jundle, args=(hpqueue, exam, 0,))
		process.start()
	return render_template('runexam.html',data=data)

@app.route("/solution/",methods=['GET', 'POST'])
@login_required
def getsol(): #def solution
	idp = request.args.get('idp')
	
	fcheck = "app/static/chambai/tmp/solution_"+str(idp)+".txt"
	if not os.path.isfile(fcheck): 
		return redirect (url_for('directlink',link="solution",arg1=idp)) 
	else: 
		os.remove(fcheck)
	
	tmp = urlparse(request.url)
	urlx = app.config['DOMAIN']#tmp.scheme +"://"+tmp.netloc + "/"

	post=Post.query.filter_by(id_p=idp).first()
	if post is None: return render_template('error.html',messeg="Không có thông tin.",data=None)
	session['meta']['title']="Hướng dẫn "+post.id_p+" - hpcode.edu.vn"
	if len(checkPinC(post))>0: return render_template('error.html',messeg="Không thể xem Hướng dẫn khi Contest chưa bắt đầu.",data=None)
	pointsub=20
	if fhp_permit(["admin","superadmin"])==1: pointsub=0
	if current_user.ndow<pointsub:return render_template('error.html',messeg="Bạn không đủ điểm.")
	link="app/static/chambai/tmp/["+current_user.username+"][hpcode]"+idp+"_sol.docx"
	if post.sol is not None:
		f=open(link,"wb")
		f.write(post.sol)
		f.close()
		current_user.ndow-=pointsub
		db.session.commit()
		link=urlx+link[4:]
		return render_template('download.html',link=link)
	return render_template('error.html',messeg="Có lỗi.")

@app.route("/getdocx/",methods=['GET', 'POST'])
@login_required
def getdocx():#tải file word cho bài tập
	idp = request.args.get('idp')
	fcheck = "app/static/chambai/tmp/getdocx_"+str(idp)+".txt"
	if not os.path.isfile(fcheck): 
		return redirect (url_for('directlink',link="getdocx",arg1=idp)) 
	else: 
		os.remove(fcheck)
	
	post=Post.query.filter_by(id_p=idp).first()
	if post is None: return render_template('error.html',messeg="Không có thông tin.",data=None)
	session['meta']['title']="Word "+post.id_p+" - hpcode.edu.vn"
	pointsub=-5
	if fhp_permit(["admin","superadmin"])==1: pointsub=0
	if current_user.ndow<pointsub:return render_template('error.html',messeg="Bạn không đủ điểm.")
	link="app/static/chambai/tmp/["+current_user.username+"][hpcode]"+idp+".docx"
	if post.docx is not None:
		f=open(link,"wb")
		f.write(post.docx)
		f.close()
		current_user.ndow-=pointsub
		db.session.commit()
		
		return render_template('download.html',link="../"+link[4:])
	return render_template('error.html',messeg="Có lỗi.")

@app.route("/admin_ql_tintuc/<int:idn>",methods=['GET', 'POST'])
@app.route("/admin_ql_tintuc/",methods=['GET', 'POST'])
def admin_ql_tintuc(idn=None):
	if fhp_permit(["superadmin","admin"])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	data={"id":-1,"title":"","content":"","err":None}
	if idn is not None:
		data["id"]=idn
		news=News.query.filter_by(id=idn).first()
		data["title"]=news.title
		data["content"]=news.content
		
	if request.method == 'POST':#Cập nhật hoặc thêm mới tin tức
		data["title"]=request.form['title']
		data["content"]=request.form.get('content')#request.form['content']
		data["id"]=int(request.form['id'])
		if data["id"]==-1:#Thêm mới
			news=News(title=data["title"],content=data["content"].replace("amp;",""),user_id=current_user.id)
			db.session.add(news)
			db.session.commit()
			data["id"]=News.query.order_by(News.id.desc()).first().id
			data["err"]="Đã thêm mới"
		else: #Cập nhật 
			news=News.query.filter_by(id=data["id"]).first()
			news.title=data["title"]
			news.content=data["content"].replace("amp;","")
			db.session.commit()
			data["err"]="Đã cập nhật"
	tmpd={"\r\n":"\\n","\n":"\\n","lqdonkh.xyz":"hpcode.edu.vn","amp;":""}
	for key in tmpd: data["content"]=data["content"].replace(key,tmpd[key])
	session['meta']['title']="Quản lý tin tức - hpcode.edu.vn"
	
	return render_template("admin_ql_tintuc.html",data=data)
@app.route("/delnew/<int:idn>")
@app.route("/delnew/")
def delnew(idn=None): #Xóa một bản tin
	
	if fhp_permit(["superadmin","admin"])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	if idn is None: return render_template("error.html",messeg="Chưa chọn bản tin cần xóa")
	new=News.query.filter_by(id=int(idn)).first()
	if new is None: return render_template("error.html",messeg="Bản tin không tồn tại")
	db.session.delete(new)
	db.session.commit()
	return render_template("error.html",messeg="Đã xóa bản tin")
@app.route("/tintuc/<int:idn>",methods=['GET', 'POST'])
@app.route("/tintuc/",methods=['GET', 'POST'])
def tintuc(idn=None):
	page = request.args.get('page', 1, type=int)
	news=News.query.order_by(News.times.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'])
	newfirst=News.query.order_by(News.times.desc()).limit(1).first()
	if idn is not None: newfirst=News.query.filter_by(id=int(idn)) .first()
	lastpage=news.pages
	news=news.items
	data={"title":"","content":"","auther":"","time":"","id":None}
	if newfirst is not None:
		data["id"]=newfirst.id
		data["title"]=newfirst.title
		data["content"]=markdown.markdown(newfirst.content.replace("amp;",""))
		data["auther"]=User.query.filter_by(id=newfirst.user_id).first().username
		data["time"]=newfirst.times
	tintuc=[]
	for tt in news:
		if tt.id==idn: continue
		tacgia=User.query.filter_by(id=tt.user_id).first().username
		tintuc.append({'idn':tt.id,"title":tt.title,"content":markdown.markdown(tt.content),"auther":tacgia,"time":str(tt.times).split(".")[0]})
	
	session['meta']['title']=data["title"]+" - hpcode.edu.vn"
	session['meta']['des']=remove_tags(data["content"][:min(len(remove_tags(data["content"])),500)]).replace("\n"," ")
	return render_template("tintuc.html",data=data,tintuc=tintuc,page=page, lastpage=lastpage)
@app.route("/admin_add_group/",methods=['GET', 'POST'])
@login_required
def admin_add_group():
	if fhp_permit(["superadmin","admin"])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	status=None
	if request.method == 'POST':
		ngroup=request.form['ngroup'].lower()
		checkauto = (request.form.getlist('checkauto')==["checked"])
		gr=Groups.query.filter_by(gname=ngroup).first()
		if gr is None:
			addgr=Groups(gname=ngroup,author=current_user.username, auto=checkauto)
			db.session.add(addgr)
			status="Đã thêm nhóm " + ngroup
		else:
			status="Tên Nhóm đã có"
		db.session.commit()
	groups=Groups.query.filter((Groups.author==current_user.username) | (Groups.author=='all')).all()
	show = None
	if fhp_permit(['superadmin']): show,groups=1,Groups.query.all()
	gr=[[g.id,g.gname,g.author] for g in groups]
	if len(gr)==0: status="Không có dữ liệu"
	session['meta']['title']="Thêm nhóm - hpcode.edu.vn"
	return render_template('admin_ql_groups.html',gr=gr,status=status,show=show)
@app.route("/admin_ql_groups/",methods=['GET', 'POST'])
@login_required
def admin_ql_groups():
	if fhp_permit(["superadmin","admin"])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	status=None
	if request.method == 'POST':
		gr=Groups.query.filter_by(id=int(request.form['idgr'])).first()
		name_user=request.form['user']
		user_id=User.query.filter_by(username=name_user).first().id
		check=Groupuser.query.filter(Groupuser.user_id==user_id,Groupuser.group_id==gr.id).first()
		if gr.author!=current_user.username and fhp_permit(['superadmin'])==0:
			return render_template("error.html",messeg="Không có quyền làm việc này")
		if request.form['action']=="Xóa": #Xóa groups
			status=" Đã xóa nhóm "+ gr.gname
			gr_user=gr.user.all()
			for ex in gr_user: db.session.delete(ex)
			db.session.delete(gr)
			db.session.commit()

		if request.form['action']=="Thêm User": #Thêm user vào groups
			status="Tài khoản "+name_user+" đã có trong groups "+ gr.gname
			if check is None:
				status="Đã THÊM "+name_user+" vào groups "+ gr.gname
				gnew=Groupuser(user_id=user_id,group_id=gr.id)
				db.session.add(gnew)
			
			db.session.commit()
			if gr.gname in ['g10d2s','g1y10s','g1y10ks1','g1y10ks2']:
				#Khi thêm user vào Groups ['g10d2s','g1y10s','g1y10ks1','g1y10ks2'] thì cộng thêm thời hạn sử dụng	
				add_user_into_groups(name_user)
				d=365
				if gr.gname == 'g10d2s': d=10
				user_ = User.query.filter_by(username=name_user).first()
				if user_.thoihan is None: user_.thoihan=datetime.strptime("09/01/2025", '%m/%d/%Y')
				if user_.thoihan < datetime.now(): user_.thoihan = datetime.now()
				user_.thoihan += timedelta(days=d)
				user_.khoatk = 0
				db.session.commit()

				
		if request.form['action']=="Xóa User": #Xóa user trong groups
			if gr.gname in ['g10d2s','g1y10s','g1y10ks1','g1y10ks2']:delete_user_into_groups(name_user)
			status="Tài khoản "+name_user+" chưa có trong groups "+ gr.gname
			if check is not None:
				status="Đã XÓA "+name_user+" khỏi groups "+ gr.gname
				db.session.delete(check)
				db.session.commit()
		
	groups=Groups.query.filter((Groups.author==current_user.username) | (Groups.author=='all')).all()
	show = None
	if fhp_permit(['superadmin']): 
		show=1
		groups=Groups.query.all()
	gr=[[g.id,g.gname,g.author] for g in groups]
	if len(gr)==0: status="Không có dữ liệu"
	session['meta']['title']="Admin: Quản lý Groups - hpcode.edu.vn"
	return render_template('admin_ql_groups.html',gr=gr,status=status,show=show)


@app.route("/admin_del_problem/",methods=['GET', 'POST'])
@login_required
def admin_del_problem():
	if fhp_permit(["superadmin","admin"])==0: return render_template('error.html',messeg="Không thể xóa bài của người khác")
	idp = request.args.get('idp')
	post=Post.query.filter_by(id_p=idp).first()
	if post is None: return render_template('error.html',messeg="Bài tập không tồn tại")
	if post.user_id!=current_user.id: return render_template('error.html',messeg="Không thể xóa bài của Admin khác")
	db.session.delete(post)
	db.session.commit()
	return render_template('error.html',messeg="Đã xóa bài tập "+idp)
	
@app.route("/listproblem/",methods=['GET', 'POST'])
def listproblem():
	err,id_p=None,""
	page = request.args.get('page', 1, type=int)
	ppp = app.config['POSTS_PER_PAGE']
	if request.method == 'POST':
		id_p=request.form['id_p'].lower()
		listp=Post.query.order_by(Post.created.desc()).filter(Post.id_p == id_p,Post.CP >= 0 ).paginate(page=page, per_page=ppp)
		if fhp_permit(["admin","superadmin"])==1:
			listp=Post.query.order_by(Post.created.desc()).filter(Post.id_p == id_p).paginate(page=page, per_page=ppp)
	if id_p=="":
		listp=Post.query.order_by(Post.created.desc()).filter(Post.CP >= 0 ).paginate(page=page, per_page=ppp)
		if fhp_permit(["admin","superadmin"])==1:
			listp=Post.query.order_by(Post.created.desc()).paginate(page=page, per_page=ppp)
	if len(listp.items)==0: err="<b>Không có dữ liệu.</b>"
	ac,problems=[],[]
	if current_user.is_authenticated:
		subac=Submitcode.query.filter(Submitcode.user==current_user.username,Submitcode.fulltest==1)
		ac=[int(x.problem) for x in subac]
	for i,p in enumerate(listp.items):
		tmp={'checkAC':""}
		#if len(checkPinC(p))>0: tmp['disabled']="btn disabled"
		if p.id in ac: tmp['checkAC']='<span class="text-success">&#10004;</span>'
		tmp['getpro']=""
		if p.docx is not None: tmp['getpro']='<span class="text-success">&#10004;</span>'		
		tmp['getsol']=""
		if p.sol is not None: tmp['getsol']='<span class="text-success">&#10004;</span>'
		allsub=Submitcode.query.filter(Submitcode.problem==p.id).count()
		allac=Submitcode.query.filter(Submitcode.problem==p.id,Submitcode.numtest==p.testcase.count()).count()
		tmp['AC']=str(allac)+"/"+str(allsub)
		tmp['checkTC']='<span class="text-success">'+str(p.testcase.count())+'</span>'
		tmp['tt']=(page-1)*ppp+1+i
		tmp['id']=p.id
		tmp['id_p']=p.id_p
		tmp['pname']=p.id_name
		if p.CP==-1: tmp['pname']="<b>*</b>"+tmp['pname']
		userx = User.query.filter(User.id==p.user_id).first()
		tmp['author']=userx.username if userx is not None  else "admin"
		problems.append(tmp)
	session['meta']['title']="Danh sách bài tập - hpcode.edu.vn"
	
	return render_template('listproblem.html',problems=problems,err=err,page=page, lastpage=listp.pages)

@app.route("/delsub/<int:idx>",methods=['GET', 'POST'])
@app.route("/delsub/",methods=['GET', 'POST'])
@login_required
def delsub(idx=None): #Xóa 1 lượt nộp bài
	if fhp_permit(["superadmin","admin"])==0:
		return render_template('error.html',messeg="Bạn không có quyền làm việc này")
	sb=Submitcode.query.filter_by(id=idx).first()
	if sb is None: return render_template('error.html',messeg="Bản ghi không tồn tại")
	db.session.delete(sb)
	db.session.commit()
	fn=str(idx)+"["+sb.user+"]["+Post.query.filter_by(id=sb.problem).first().id_p+"]."+sb.ext
	fn=os.path.join("app/static/chambai/baihs",fn)
	try:
		os.remove(fn)
	except:
		print("error")
	return redirect('/listsubmit/')

@app.route("/delsubex/<int:idx>",methods=['GET', 'POST'])
@app.route("/delsubex/",methods=['GET', 'POST'])
@login_required
def delsubex(idx=None): #Xóa 1 lượt nộp ví dụ
	
	if fhp_permit(["superadmin","admin"])==0:
		return render_template('error.html',messeg="Bạn không có quyền làm việc này")
	sb=Runexam.query.filter_by(id=idx).first()
	if sb is None: return render_template('error.html',messeg="Bản ghi không tồn tại")
	db.session.delete(sb)
	db.session.commit()
	return redirect('/listexam/')

@app.route("/listsubmit/",methods=['GET', 'POST'])
def listsubmit():
	err=None
	user=request.args.get('tag')
	page = request.args.get('page', 1, type=int)
	if request.method == 'POST':
		user=request.form['user'].lower()
		if user=="none": user=None
	
	listsub=[]
	

	if user is None:
		lists=Submitcode.query.order_by(Submitcode.id.desc())
	else:
		lists=Submitcode.query.order_by(Submitcode.id.desc()).filter(Submitcode.user==user)
	
	lists=lists.paginate(page=page, per_page=app.config['POSTS_PER_PAGE'])
	if lists.items is None: err="<b>Không có dữ liệu.</b>"
	
	for i,s in enumerate(lists.items):
		user = User.query.filter_by(username=s.user).first()
		pr=Post.query.filter_by(id=s.problem).first()
		if pr is None: continue

		tmp={"numtest":s.numtest,"alltest":pr.testcase.count(),"user":s.user,"id_p":pr.id_p,"ext":s.ext,"time":(str(s.timesb)+'.').split(".")[0],"idp":pr.id,"ids":s.id,"checkcode":0}
		if fhp_permit(["superadmin","admin"])==1: tmp["checkcode"] = 1
		if current_user.is_authenticated:
			if current_user.username==s.user: tmp["checkcode"] = 1
			if current_user.giaovien==1 and Giaovienhs.query.filter(Giaovienhs.hs_id==user.id, Giaovienhs.gv_id==current_user.id).first() is not None:
				tmp["checkcode"] = 1
		listsub.append(tmp)
	
	session['meta']['title']="Danh sách nộp bài - hpcode.edu.vn"
	
	return render_template('listsubmit.html',listsub=listsub,err=err,page=page, lastpage=lists.pages)
@app.route("/listexam/",methods=['GET', 'POST'])
@login_required
def listexam():
	if fhp_permit(["superadmin","admin"])==0:
		return render_template('error.html',messeg="Bạn không có quyền làm việc này",data=None)
	err=None
	lists=Runexam.query.all()
	for i in range(len(lists)-1001): db.session.delete(lists[i])
	db.session.commit()
	lists=Runexam.query.order_by(Runexam.id.desc()).limit(100)
	
	if lists is None: err="<b>Không có dữ liệu.</b>"
	listsub=[]
	for i,s in enumerate(lists):
		pr=Post.query.filter_by(id=s.idp).first()
		if pr is None: continue
		tmp={"user":s.user,"id_p":pr.id_p,"ext":s.ext,"idp":pr.id,"ids":s.id,"graded":s.graded}
		listsub.append(tmp)
	session['meta']['title']="Danh sách nộp bài ví dụ - hpcode.edu.vn"
	return render_template('listexam.html',listsub=listsub)

@app.route("/adminproblem/",methods=['GET', 'POST']) # Thêm hoặc sửa nội dung bài tập
@login_required
def adminproblem():
	session['meta']['title']="Thêm bài tập - hpcode.edu.vn"
	if fhp_permit(["superadmin","admin"])==0:
		return render_template('error.html',messeg="Bạn không có quyền làm việc này",data=None)
	err=None
	idp = request.args.get('idp')
	post=Post.query.filter_by(id_p=idp).first()
	if post is not None: session['meta']['title']="Edit: "+post.id_p+" - hpcode.edu.vn"
	#trường hợp sửa bài tập sẽ không cho sửa bài của người khác
	if fhp_permit(["superadmin"])==0:
		if post is not None and post.user_id!=current_user.id: 
			return render_template('error.html',messeg="Không thể thực hiện với bài tập của người khác")
	if request.method == 'POST':
		id_p=request.form['id_p'].lower()
		id_name=request.form['id_name']
		source = request.form['source']
	
		post = Post.query.filter_by(id_p=id_p).first()
		if post is not None:
			if post.user_id!=current_user.id and current_user.username!="admin": return render_template('error.html',messeg="Không thể thêm/xóa của người khác")
			post.id_p,post.id_name,post.source=id_p,id_name,source
			err="Đã cập nhật bài tập "+id_p
			session['meta']['title']="Edit: "+post.id_p+" - hpcode.edu.vn"
		else:
			post=Post(id_p=id_p,id_name=id_name,user_id=current_user.id,source=source)
			db.session.add(post)
			err="Thêm mới thành công"
			session['meta']['title']="Add: "+post.id_p+" - hpcode.edu.vn"
			fname = "app/static/data/post.txt"
			f=open(fname,"a",encoding="utf-8")
			f.write(id_p+"@"+id_name+"\n")
			f.close()
		file = request.files['file_docx']
		filename = secure_filename(file.filename).lower()
		if "." in file.filename and filename.split(".")[-1]  in ["docx"]:
			linkt=os.path.join("app/static/chambai/tmp",filename)
			file.save(linkt)
			
			# Convert the docx file to pdf using docx2pdf
			tmp_pdf_path = linkt.replace(".docx", ".pdf")
			docx2pdf.convert(linkt, tmp_pdf_path)

			# Read the pdf file content
			with open(tmp_pdf_path, "rb") as pdf_file:
				post.pdf = pdf_file.read()
			with open(linkt, "rb") as docx_file:
				post.docx=docx_file.read()
			post.body = docx2html(linkt,post.id_p) #chuyển đổi từ docx sang html
	
		db.session.commit()
		processtags(request.form['tag'],post.id)
		config=Config.query.filter_by(idp=post.id).first()

		if config is None:
			config=Config(idp=post.id,juger=request.form['tc'],tlexe=float(request.form['exe']),
				tlpy=float(request.form['py']),exp=float(request.form['e']))
			db.session.add(config)
		else:
			config.juger=request.form['tc']
			config.tlexe=1 if request.form['exe']=="" else float(request.form['exe'])
			config.tlpy=2 if request.form['py']=="" else float(request.form['py'])
			config.exp=0.00001 if request.form['e']=="" else float(request.form['e'])
		db.session.commit()
		
	tag=""
	config=Config(tlexe=1,tlpy=2,juger='c1',exp=0.00001,memory=1024)
	if post is not None:
		config=Config.query.filter_by(idp=post.id).first()
		for tag_id in post.tag_id.all():
			tgx=Tags.query.filter_by(id=tag_id.id_tag).first()
			if tgx is not None: tag=tag+tgx.tagname+', '
		if len(tag)>=2: tag=tag[:-2]
	
	listp= [post.id_p for post in Post.query.all()]
	
	return render_template('admin_problem.html',err=err,post=post,conf=config,tag=tag,listp=listp)
@app.route('/mte/',methods=['GET', 'POST'])
def mte():
	idx = request.args.get('idx')
	if idx is None: idx="01"
	mte={"01":{"name":"Bài giảng Ancol (tiết 1) - Hóa học lớp 11","link":"https://bit.ly/3BHEpnH"},
	     "02":{"name":"Tóm tắt Thành phần nguyên tử hóa học - Hóa học lớp 10","link":"https://bit.ly/3rWJ8yv"}
	    }
	return render_template('mte.html',curr=idx,mte=mte)

@app.route("/ranking/<string:cname>",methods=['GET', 'POST'])#Xếp hạng cho từng Contest
@app.route('/ranking/',methods=['GET', 'POST'])
def ranking(cname=None):
	data,fullname,maxpoint={},{},{} #maxpoint là điểm tối đa của một bài tập trong Contest, vd: maxpoint['beehive']=10
	fulluser= []
	#Dành cho các Contest chấm bằng Themis
	if cname.lower() in ["contest01","contest02","contest03","contest04","contest05","contest06","contest06x","contest08"]:
		root=os.path.join("app/static/themis/oj/logs",cname)
		listp=[]
		for fn in os.listdir(root):
			f=open(os.path.join(root,fn),"r",encoding="utf-8")
			info = f.readline()
			f.close()
			mark = info.split()[1].replace(".","") 
			tmp= fn.replace("]"," ").replace("["," ")
			user = tmp.split()[1].lower()
			pro = tmp.split()[2].lower()
			if pro not in listp: listp.append(pro)
			if user not in data: data[user]={}
			if pro not in data[user]: data[user][pro]=0
			if mark.isnumeric(): data[user][pro]=max(data[user][pro],float(info.split()[1]))
			userx = User.query.filter_by(username=user).first()
			fullnamex = userx.fullname if userx is not None else "Không xác định"
			if user not in fullname: fullname[user]=fullnamex
		return render_template('ranking.html',data=data,post=listp,name="Themis: "+string.capwords(cname) ,fullname=fullname)

	tag=Tags.query.filter(Tags.tagname==cname,Tags.ts!=Tags.te).first() #Lấy kỳ thi
	if tag is None: return render_template('error.html',messeg="Không tìm thấy Contest",data=None)
	listp= [] #Lấy danh sách bài tập trong theo đúng thứ tự trong Contest
	for p in tag.post_id.all():
		tp=Tag_post.query.filter_by(id=p.id).first()
		post = Post.query.filter_by(id=tp.id_post).first()
		maxpoint[post.id_p]=tp.point
		listp.append([tp.no,post.id_p])
	tmp_listp=sorted(listp,key=lambda x: x[0])
	listp = [x[1] for x in tmp_listp]

	gr=Groups.query.filter_by(id=tag.limit).first() #Lấy đối tượng tham gia kỳ thi	
	for tmp in gr.user.all():
		userid = Groupuser.query.filter_by(id=tmp.id).first()
		user = User.query.filter_by(id=userid.user_id).first()
		fulluser.append(user.username)
		fullname[user.username]=user.fullname
	for user in fulluser:
		tmp,check={},0
		
		for r in Rank.query.filter(Rank.user==user).all():
			if r.problem not in listp: continue
			tl = r.numtest/r.alltest #Tỉ lệ số test đúng/tổng số test
			tmp[r.problem]=round(tl*maxpoint[r.problem],2)
			check=1
		if check==1: data[user]=tmp
	return render_template('ranking.html',data=data,post=listp,name=tag.tagtitle,fullname=fullname)


@app.route("/resetranking/",methods=['GET', 'POST'])
@login_required
def resetranking():
	session['meta']['title']="Reset bảng xếp hạng - hpcode.edu.vn"
	try:
		if fhp_permit(['superadmin'])==0: return render_template('error.html',messeg="Truy cập bị từ chối")
		if request.method == 'POST':
			cname = request.form['cname']
			hpranking(cname)
			tag = Tags.query.filter_by(tagname=cname).first()
			session['meta']['title']="Reset bảng xếp hạng "+tag.tagtitle +"- hpcode.edu.vn"
		return render_template('resetranking.html')
	except Exception as e:
		f=open("Error.txt","a",encoding="utf-8")
		f.write("\n\n"+str(e)+"\n\n")
		f.close()
		print(str(e))
	return render_template('error.html',messeg="Có lỗi")
@app.route("/listuser/",methods=['GET', 'POST'])
@login_required
def listuser():
	error,infoacc,update=None,None,None
	if fhp_permit(['admin','superadmin'])==0: return render_template('error.html',messeg="Truy cập bị từ chối")
	if request.method == 'POST':
		user = User.query.filter_by(username=request.form['fusername']).first()
		if user is None:
			error = " Không tìm thấy tài khoản, hãy kiểm tra lại"
		else:
			if request.form.get('Update'):
				update="Update: "
				if request.form.get('resetpass'):
					user.set_password('haiphongoj')
					update=update+" Mật khẩu "
				if request.form.get('deleteacc'): 
					error="Chỉ có superadmin mới có quyền xóa User"
					if fhp_permit(['superadmin'])==1:
						db.session.delete(user)
						error="Đã xóa"
				db.session.commit()
			if error!="Đã xóa":
				permit=[Groups.query.filter_by(id=int(gr.group_id)).first().gname for gr in user.group.all() ]
				infoacc=[user.username,user.fullname,user.email,permit]
	listgr={}
	tmpgr=Groups.query.all()
	for gr in tmpgr:
		listgr[gr.gname]=[]
		for user in gr.user.all():
			userx=User.query.filter_by(id=user.user_id).first()
			if userx is None: 
				db.session.delete(user)
				db.session.commit()
				continue
			listgr[gr.gname].append(userx.username)
	session['meta']['title']="Danh sách User - hpcode.edu.vn"
	return render_template('listuser.html',error=error,infoacc=infoacc,update=update,listgr=listgr)

@app.route('/changeimg/',methods=['GET', 'POST'])
@login_required
def changeimg():
	if request.method == 'POST':
		file = request.files['file']
		if file.filename == '': return redirect('/info')
		if file.filename.lower().split('.')[-1] not in ['jpg','png']: return redirect('/info')

		filename = secure_filename(file.filename)
		filename = current_user.username + '.' + filename.split('.')[1]
		
		fn = 'app/static/chambai/tmp/'+filename
		file.save(fn)
		with open(fn, "rb") as image_file:
			current_user.imgbase64 = base64.b64encode(image_file.read()).decode(encoding='utf-8')
		db.session.commit()
		
		return redirect('/info')

@app.route('/changepass/',methods=['GET', 'POST'])
@login_required
def changepass():
	
	err = None
	if current_user.username=="hpelearning": err="Không được phép đổi mật khẩu"
	if request.method == 'POST' and current_user.username!="hpelearning":
		if not current_user.check_password(request.form['oldpass']):
			err=" Sai mật khẩu"
		if request.form['newpass']=='':
			err=" Mật khẩu không được để trống"
		if request.form['newpass']!=request.form['repass']:
			err=" Mật khẩu không giống nhau"
		if err is not None:	return redirect(url_for('info',errpass=err))#return render_template('info.html',errpass=err)

		current_user.set_password(request.form['newpass'])
		db.session.add(current_user)
		db.session.commit()
		err = "Thành công!"
	return redirect(url_for('info',errpass=err))

@app.route('/info/',methods=['GET', 'POST'])
@app.route('/info/<string:user>',methods=['GET', 'POST'])
def info(user=None):
	
	errpass=request.args.get('errpass')
	if user is None:
		if current_user.is_authenticated: userx=current_user
		else: return render_template('error.html',messeg="Không tìm thấy tài khoản",data=None)
	else:
		userx=User.query.filter_by(username=user).first()
	if userx is None: return render_template('error.html',messeg="Không tìm thấy tài khoản",data=None)
	session['meta']['title']=userx.fullname
	
	if '@' not in userx.email: 
		be,ap=userx.email,''
	else:
		be,ap=userx.email.split("@")
	email=be[:1]+'*'*(len(be)-2)+be[-1]+"@"+ap
	if fhp_permit(["admin","superadmin"])==1: email=userx.email
	data={"groups":[],"email":email,"fullname":userx.fullname,"username":userx.username,"ndow":"","AC":[]}
	data['khoatk'] = userx.khoatk if userx.khoatk in [0,1] else 0 # 0 = không khóa
	data["ndow"]=str(userx.ndow)
	#Lấy danh sách groups của User
	try:
		data["groups"]=[string.capwords(Groups.query.filter_by(id=g.group_id).first().gname) for g in userx.group.all()]
	except:
		data["groups"]=""
	#Lấy danh sách các bài tập User đã Accept
	data["sb"]={} #Lấy danh sách bài làm đã nộp theo ngày
	for sb in Submitcode.query.filter_by(user=userx.username).order_by(Submitcode.timesb.desc()).all():
		post = Post.query.filter_by(id=sb.problem).first()
		if post is None: continue
		dayx = str(sb.timesb).split(" ")[0].split("-")
		day = dayx[2]+"-"+dayx[1]+"-"+dayx[0] #Lấy ngày tháng năm
		if day not in data["sb"]: data["sb"][day]={"AC":[],"WA":[]}
		if sb.fulltest==1: #Chỉ lấy các bài đã chấm fulltest
			if post.id_p not in data["sb"][day]["AC"]:
				data["sb"][day]["AC"].append(post.id_p)
		else:
			if post.id_p not in data["sb"][day]["WA"]:
				data["sb"][day]["WA"].append(post.id_p)
	for key in data["sb"]:
		for p in data["sb"][key]["AC"]:
			if p in data["sb"][key]["WA"]: data["sb"][key]["WA"].remove(p) #Xóa các bài đã AC khỏi danh sách WA

	data['xacthuc'] = userx.xacthuc if userx.xacthuc in [0,1] else 0 # 0 = Chưa xác thực
	data['thoihaninfo'] = userx.thoihan
	
	return render_template('info.html',errpass=errpass,data=data)
@app.route("/signup/",methods=['GET', 'POST'])
def signup():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	if request.method == 'POST':
		err = None
		if request.form['password']!=request.form['Repassword']:err=" Mật khẩu không giống nhau"
		username = request.form['username']
		if len(username)>15 or len(request.form['username'])<6: err= "Tên đăng nhập có tối thiểu 6 ký tự và tối đa 15 ký tự"
		if err is not None: return render_template('signup.html',error=err)
		user = User.query.filter_by(username=username).first()
		if user is not None: 
			err = " Tên đăng nhập đã có. Hãy chọn tên khác!"
			return render_template('signup.html',error=err)

		user = User.query.filter_by(email=request.form['email']).first()
		if user is not None:
			err = "Email đã có. Hãy chọn Email khác!"
			return render_template('signup.html',error=err)	
		
		fn = 'app/static/lhp.jpg'
		imgbase64=""
		with open(fn, "rb") as image_file: imgbase64 = base64.b64encode(image_file.read()).decode(encoding='utf-8')

		user = User(username=request.form['username'], email=request.form['email'], fullname=request.form['fullname'],langdf = request.form['lang'],thoihan=datetime.now()+timedelta(days=30),imgbase64=imgbase64)
		user.set_password(request.form['password'])
		db.session.add(user)
		db.session.commit()

		#Thêm vào học sinh
		user = User.query.filter_by(username=username).first()
		gv = User.query.filter_by(username='giaovien30').first()
		if gv is None:
			gv = User(username='giaovien30',giaovien=1)
			gv.set_password("A@a01Zz")
			db.session.add(gv)
			db.session.commit()
		gv = User.query.filter_by(username='giaovien30').first()
		gvhs = Giaovienhs(gv_id=gv.id, hs_id=user.id)
		db.session.add(gvhs)
		db.session.commit()

		err = "Đăng ký thành công. Hãy đăng nhập!"
		return redirect(url_for('login'))
	else:
		session['meta']['title']="Đăng kí tài khoản - hpcode.edu.vn"
		return render_template('signup.html')

@app.route("/signuphs/",methods=['GET', 'POST']) #Cho phép giáo viên đăng ký học sinh
@login_required
def signuphs():
	#return render_template('error.html',messeg="Chức năng này đã bị hủy")
	if current_user.giaovien!=1: return render_template('error.html',messeg="Chức năng này chỉ dành cho giáo viên")
	
	if request.method == 'POST':
		err=None	
		username = request.form['username']
		if len(username)>15 or len(request.form['username'])<6: err= "Tên đăng nhập có tối thiểu 6 ký tự và tối đa 15 ký tự"
		if err is not None: return render_template('signuphs.html',error=err)
		user = User.query.filter_by(username=username).first()
		if user is not None: 
			err = " Tên đăng nhập đã có. Hãy chọn tên khác!"
			return render_template('signuphs.html',error=err)

		user = User.query.filter_by(email=request.form['email']).first()
		if user is not None:
			err = "Email đã có. Hãy chọn Email khác!"
			return render_template('signuphs.html',error=err)	
		
		fn = 'app/static/lhp.jpg'
		imgbase64=""
		with open(fn, "rb") as image_file: imgbase64 = base64.b64encode(image_file.read()).decode(encoding='utf-8')

		user = User(username=request.form['username'], email=request.form['email'], fullname=request.form['fullname'],langdf = request.form['lang'],thoihan=datetime.now()+timedelta(days=365),imgbase64=imgbase64)
		user.set_password("haiphongoj")
		db.session.add(user)
		db.session.commit()
		gvhs = Giaovienhs(gv_id=current_user.id, hs_id=user.id)
		db.session.add(gvhs)
		db.session.commit()

		err = "<span class='text-success'>Đăng ký thành công!</span><br>Mật khẩu mặc định của <b>"+username+"</b> là <b>haiphongoj</b>. Hãy đăng nhập và đổi mật khẩu."
		#return redirect(url_for('signup',error=err))
		return render_template('signuphs.html',error=err)
	else:
		session['meta']['title']="Đăng kí tài khoản - hpcode.edu.vn"
		return render_template('signuphs.html')
# Route for handling the login page logic
@app.route("/login/",methods=['GET', 'POST'])
def login():
	
	session['meta']['title']="Đăng nhập - hpcode.edu.vn"
	try:
		err=None
		hpnext=request.args.get('hpnext') #chuyển tiếp chủ động
		if current_user.is_authenticated:
			return redirect(url_for('index'))
		
		if request.method == 'POST':
			user = User.query.filter_by(username=request.form['username']).first()
			if user is None :
				err=" Sai tên đăng nhập"
				return render_template('login.html',error=err)
			if not user.check_password(request.form['password']):
				err=" Sai mật khẩu"
				return render_template('login.html',error=err)    	
			login_user(user, remember=False)
			lastlogin=History(ip=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),user_id=current_user.id)
			db.session.add(lastlogin)
			db.session.commit()
			if current_user.langdf is None: return render_template('setdef.html')

			next_page = request.form['next']
			if hpnext is not None: return redirect(hpnext)
			if not next_page or url_parse(next_page).netloc != '': next_page = url_for('index')
			
			return redirect(next_page)
		return render_template('login.html',error=err)
	except Exception as e: 
		print(e)
		writelogerr(e)
	return "Loi"

@app.route('/history/')
def history():
	
	session['meta']['title']="Lịch sử đăng nhập - hpcode.edu.vn"
	try:
		data=[]
		page = request.args.get('page', 1, type=int)
		h=History.query.order_by(History.timel.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'])
		lastpage=h.pages
		h=h.items
		for i in range(len(h)):
			fn=User.query.filter_by(id=h[i].user_id).first()
			if fn is None: continue
			fn=fn.username
			timez=str(h[i].timel).split(".")[0]
			ip="111.111.111.111"
			if fhp_permit(["superadmin","admin"]): ip=h[i].ip
			data.append([(page-1)*app.config['POSTS_PER_PAGE']+1+i,fn,ip,timez,""])
		return render_template('history.html',data=data,page=page, lastpage=lastpage)
	except Exception as e: writelogerr(e)
	return render_template('error.html',messeg="Có lỗi")
@app.route('/logout/')
@login_required
def logout():
	logout_user()
	next_page = request.args.get('next')
	if not next_page or url_parse(next_page).netloc != '':
		next_page = url_for('login')
	print(next_page)
	return redirect(next_page)

@app.route("/vtinhoc/",methods=['GET', 'POST'])
@app.route("/vtinhoc/<int:sott>",methods=['GET', 'POST'])
def vtinhoc(sott=0):
	
	status=None
	
	session['meta']['title']="hpcode.edu.vn"
	lid=[vid for vid in Ytbe.query.order_by(Ytbe.id.desc()).all()]

	if request.method == 'POST':
		url=request.form['url']
		if "www.youtube.com/watch?v=" not in url: 
			status="Link YouTube không đúng định dạng"
			return render_template('vtinhoc.html',lid=lid,status=status)		
		
		idv=url.split("=")[1]
		vid=Ytbe.query.filter_by(idv=idv).first()
		status="Video đã có. Các thông tin của video sẽ được cập nhập"
		yt = YouTube(url)
		dura=str(yt.length/60)+":"+str(yt.length%60)
		if vid is None:
			new_yt=Ytbe(idv=idv,views=yt.views,title=yt.title,descr=yt.description,datep=yt.publish_date,duration=dura,thumb=yt.thumbnail_url)
			lid.insert(0,new_yt)
			status="Đã thêm video "+yt.title
			db.session.add(new_yt)
		else:
			vid.views=yt.views
			vid.title=yt.title
			vid.descr=yt.description
			vid.datep=yt.publish_date
			vid.duration=dura
			vid.thumb=yt.thumbnail_url
		db.session.commit()
	session['meta']['title']="Video - hpcode.edu.vn"
	if len(lid)==0:
		status="Chưa có Video"
	else:
		tmp=lid[sott]
		lid.pop(sott)
		lid.insert(0,tmp)
		session['meta']['title']=lid[0].title+" - hpcode.edu.vn"
	return render_template('vtinhoc.html',lid=lid,status=status)

@app.route("/translate/",methods=['GET', 'POST'])
def translate():
	
	session['meta']['title']="Dịch ngôn ngữ - hpcode.edu.vn"
	f=open("language.txt","r")
	dictl=eval(f.read())
	lid=[]
	lla=[]
	lid.append('vi')
	lla.append(dictl['vi'])
	lid.append('en')
	lla.append(dictl['en'])
	for key in dictl:
		if(key!='vn' or key!='en'):
			lid.append(key)
			lla.append(dictl[key])
	scrtext="Nhập văn bản vào đây"
	desttext="Văn bản được dịch ở đây"
	if request.method == 'POST':
		scrtext=request.form['scrtext']
		scr=request.form['scr']
		dest=request.form['dest']
		translator = Translator()
		translated = translator.translate(scrtext, src=scr, dest=dest)
		desttext =translated.text
	return render_template('translate.html',lid=lid,lla=lla,scrtext=scrtext,desttext=desttext)
@app.route("/addviewcontest/",methods=['GET', 'POST'])   
@app.route("/addviewcontest/<string:tagname>",methods=['GET', 'POST'])
@login_required
def addviewcontest(tagname=None):
	
	tag=Tags.query.filter_by(tagname=tagname).first()
	if tag is None: return render_template('error.html',messeg="Hãy chọn Contest có sẵn.",data=None)
	if fhp_permit(["superadmin"])==0: return render_template('error.html',messeg="Bạn không có quyền làm việc này",data=None)
	x,_=checkTimeInOnline(tag.ts,tag.te)
	if x!=1: return render_template('error.html',messeg="Chức năng này chỉ được thực hiện khi hết giờ",data=None)
	if tag.addview==True: return render_template('error.html',messeg="Đã được cập nhật trước đó",data=None)
	tag.addview=True

	data={}
	for p in tag.post_id.all():
		post=Post.query.filter_by(id=p.id_post).first()
		tp=Tag_post.query.filter(Tag_post.id_tag==tag.id,Tag_post.id_post==p.id_post).first()
		point=10 if tp is None or tp.point is None else tp.point
		sub=Submitcode.query.filter(Submitcode.problem==p.id_post,Submitcode.timesb>tag.ts,Submitcode.timesb<=tag.te).all()
		for sb in sub:
			if sb.user not in data: data[sb.user]={}
			if p.id_post not in data[sb.user]: data[sb.user][p.id_post]=0
			data[sb.user][p.id_post]=max(float(sb.numtest)/post.testcase.count()*point,data[sb.user][p.id_post])
	for key in data:
		user=User.query.filter_by(username=key).first()
		for x in data[key]: user.ndow=user.ndow+data[key][x]
	db.session.commit()
	return redirect (url_for('contest',tagname=tagname))
@app.route("/contest/",methods=['GET', 'POST'])   
@app.route("/contest/<string:tagname>",methods=['GET', 'POST'])
def contest(tagname=None):
	try:
		tag=Tags.query.filter_by(tagname=tagname).first()
		if tag is None: return render_template('error.html',messeg="Hãy chọn Contest có sẵn.",data=None)
		groups=Groups.query.filter_by(id=tag.limit).first()
		if groups is None: return render_template('error.html',messeg="Hãy chọn Contest có sẵn.",data=None)
		groups=groups.gname

		if tag.ts==tag.te: return redirect (url_for('viewtag',tag=tag.tagname))
		#Reset Bảng xếp hạng hoặc thêm lượt xem cho người nếu ... 
		times={"time_b":tag.ts,"time_e":tag.te}
		total,post=0,[]
		maxsub = solannpbaiconlai()
		for px in tag.post_id.all():
			p=Post.query.filter_by(id=px.id_post).first()
			if p is None: continue
			dethitinh,dethiyear=None,None
			if p.de_id.first() is not None:
				dethi = Dethi.query.filter_by(id=p.de_id.first().id_dethi).first()
				dethitinh,dethiyear=dethi.tinh,dethi.year2
			
			listtg=[]
			if tag.tagname in app.config['SHOWTAGS']: listtg=getalltag(p)#Lấy toàn bộ tag của bài tập p
			slsub="-/-"
			tp=Tag_post.query.filter(Tag_post.id_tag==tag.id,Tag_post.id_post==p.id).first()
			point=10 if tp is None or tp.point is None else tp.point
			AC,result=0,0
			
			if current_user.is_authenticated:
				sub=Submitcode.query.filter(Submitcode.user==current_user.username,Submitcode.problem==p.id,Submitcode.timesb<=tag.te).order_by(Submitcode.numtest.desc())
				sb=sub.first()
				if sb is not None and sb.numtest is not None:
					if p.testcase.count()>0 and sb.numtest >0: result=round(sb.numtest/p.testcase.count()*point,2)
					if sb.numtest<p.testcase.count() and sb.numtest>0 and AC==0: AC=1
					if sb.numtest==p.testcase.count(): AC=2
				total=total+result
				slsub=str(sub.count())+'/'+str(maxsub)
			tp=Tag_post.query.filter(Tag_post.id_tag==tag.id,Tag_post.id_post==p.id).first().no
			
			post.append({"cp":tp if str(tp).replace('.','').isnumeric() else 100,"idp":p.id_p.lower(), \
				"name":p.id_name,"id":p.id,"slsub":slsub,"maxm":result,"AC":AC,"listtg":listtg,\
				"tinh":dethitinh, "year" : dethiyear})
		post=sorted(post,key=lambda x: (x['cp'],x['AC']))
		
		session['meta']['title']=tag.tagname+" - hpcode.edu.vn"
		showtinhdethi = 1 if tagname in ["ts10","thcs","hsga","hsgb"] else None
		if showtinhdethi == 1: post=sorted(post,key=lambda x: (x['year'],x['tinh']))
		return render_template('contest.html',post=post,total=total,times=times,tag=tag,groups=groups,showtinhdethi=showtinhdethi,checkads=1)
	except Exception as e:
		f=open("Error.txt","a",encoding="utf-8")
		f.write("\n\n"+str(e)+"\n\n")
		f.close()
		print(str(e))
	return render_template('error.html',messeg="Error!.",data=None)

@app.route("/viewlog/<string:ids>",methods=['GET', 'POST'])
def viewlog(ids=None):
	
	if ids is None: return "Có lỗi"

	ids = int(ids.split("#")[0])
	sb=Submitcode.query.filter_by(id=ids).first()
	if sb is None: return "Có lỗi"
	data=str(sb.log).replace("\n","<br>")
	
	session['meta']['title']="Log["+sb.user+"]["+Post.query.filter_by(id=sb.problem).first().id_p+"]."+sb.ext+" -hpcode.edu.vn"
	title = "["+sb.user+"]["+Post.query.filter_by(id=sb.problem).first().id_p+"."+sb.ext+"]"
	if current_user.is_authenticated: return render_template('viewlog.html',data=data,title=title)
	return redirect (url_for('login'))

@app.route("/viewtag/",methods=['GET', 'POST'])
@app.route("/viewtag/<string:tag>",methods=['GET', 'POST'])
def viewtag(tag=None):
	
	err=None
	tag_=Tags.query.filter_by(tagname=tag).first()
	if tag_==None: return "Không có dữ liệu"
	if tag_.ts!=tag_.te: return redirect (url_for('contest',tagname=tag_.tagname))
	
	post=[Post.query.filter(Post.id==p.id_post,Post.CP==0).first() for p in tag_.post_id.all()]
	
	if fhp_permit(["admin","superadmin"])==1:
		post=[Post.query.filter(Post.id==p.id_post).first() for p in tag_.post_id.all()]
	if len(post)==0: err="<b>Không có dữ liệu.</b>"
	ac=[]
	if current_user.is_authenticated:
		subac=Submitcode.query.filter(Submitcode.user==current_user.username,Submitcode.fulltest==1)
		ac=[int(x.problem) for x in subac]

	problems=[]
	for i,p in enumerate(post):
		if p is None: continue
		tmp={'checkAC':""}
		if current_user.is_authenticated and p.id in ac: tmp['checkAC']='<span class="text-success">&#10004;</span>'
		tmp['getpro']=""
		tmp['getsol']=""
		tmp['AC']=str(p.ac)+"/"+str(p.allsub)
		tmp['checkTC']='<span class="text-success">'+str(p.testcase.count())+'</span>'
		tmp['id']=p.id
		tmp['id_p']=p.id_p
		tmp['pname']=p.id_name
		tmp['author']=User.query.filter_by(id=p.user_id).first().username if User.query.filter_by(id=p.user_id).first() is not None else ""
		tmp['disabled']=''
		if len(checkPinC(p))>0: tmp['disabled']=''#'btn disabled'
		tx=Tag_post.query.filter(Tag_post.id_tag==tag_.id,Tag_post.id_post==p.id).first().no
		tmp['no']= float(tx) if str(tx).replace('.','').isnumeric() else 100
		problems.append(tmp)
	
	session['meta']['title']=tag_.tagtitle+" - hpcode.edu.vn"
	return render_template('viewtag.html',problems=sorted(problems, key=lambda d: d['no']), tag=tag,tagdata=tag_)

@app.route("/admin_delprtag",methods=['GET', 'POST'])
@login_required
def admin_delprtag():#xóa một bài tập trong Tag/Contest
	
	if fhp_permit(['admin','superadmin'])==0: return "bạn không có quyền làm việc này"
	id_p=request.args.get('id_post')
	tagid = int(request.args.get('id_tag'))
	tag=Tags.query.filter_by(id=tagid).first()
	if current_user.username!=tag.user: return "bạn không có quyền thay đổi Tag/Contest của "+ tag.user
	idp=Post.query.filter_by(id_p=id_p).first().id
	pt=Tag_post.query.filter(Tag_post.id_tag==tagid,Tag_post.id_post==idp).first()
	db.session.delete(pt)
	db.session.commit()
	return redirect (url_for('admin_ql_tags',tagname=tag.tagname))
@app.route("/admin_del_contest/",methods=['GET', 'POST'])
@login_required
def admin_del_contest():
	
	if fhp_permit(['admin','superadmin'])==0: return "bạn không có quyền làm việc này"
	tagname = request.args.get('tagname')
	tag=Tags.query.filter_by(tagname=tagname).first()
	if tag is None:
		return render_template('error.html',messeg="Contest/Tag không tồn tại")
	if tag.user!=current_user.username:
		return render_template('error.html',messeg="Không được xóa Contest/Tag của "+tag.user)
		
	if tag.post_id.count()>0: return render_template('error.html',messeg="Hãy xóa hết bài tập trong Tag/Contest "+ tagname+ "trước khi xóa")
	for tp in tag.post_id.all(): db.session.delete(tp)
	db.session.delete(tag)
	db.session.commit()
	return redirect (url_for('listcontest'))
@app.route("/admin_ql_tags/",methods=['GET', 'POST'])
@login_required
def admin_ql_tags():
	
	session['meta']['title']="Admin - quản lí Tags/Contest - hpcode.edu.vn"
	if fhp_permit(['admin','superadmin'])==0: return "bạn không có quyền làm việc này"
	tagname = request.args.get('tagname')
	if request.method == 'POST' and request.form['submit']=="Update":
		tagname=request.form['tagname'].lower()
		tag=Tags.query.filter_by(tagname=tagname).first()
		if tag is None:
			tag=Tags(tagname=tagname)
			db.session.add(tag)
			db.session.commit
		elif current_user.username!=tag.user: return "bạn không có quyền thay đổi Tag/Contest của "+ tag.user
		
		tag.tagtitle=request.form['tagtitle']
		tag.taglink=request.form['taglink']
		tag.ts=conertTimeHTMLtoPython(request.form['timeb'])
		tag.te=conertTimeHTMLtoPython(request.form['timee'])
		print(tag.ts,tag.te)
		tag.limit=int(request.form['groups'])
		tag.user=current_user.username
		db.session.commit()
		session['meta']['title']="Admin - Cập nhật"+ tag.tagtitle  +"- hpcode.edu.vn"
	if request.method == 'POST' and request.form['submit']=="Delete":
		tagname=request.form['tagname'].lower()
		tag=Tags.query.filter_by(tagname=tagname).first()
		if tag is None: return render_template('error.html',messeg="Tag/Contest không tồn tại")
		# if tag.post_id.count()>0:
		# 	return render_template('error.html',messeg="Hãy xóa hết bài tập trong Tag/Contest "+ tagname+ "trước khi xóa")
		if current_user.username!=tag.user: return "bạn không có quyền thay đổi Tag/Contest của "+ tag.user
		for idp in tag.post_id.all():
			db.session.delete(idp)
			db.session.commit()
		session['meta']['title']="Admin - Xóa"+ tag.tagtitle  +"- hpcode.edu.vn"
		db.session.delete(tag)
		db.session.commit()
		return render_template('error.html',messeg="Đã xóa "+ tagname)

	groups,listpr=[],[]
	for g in Groups.query.all():
		groups.append({"id":g.id,"gname":g.gname})
	data=Tags.query.filter_by(tagname=tagname).first()
	if data is not None:
		session['meta']['title']="Admin - Quản lí: "+ data.tagtitle  +"- hpcode.edu.vn"
		if data.user!=current_user.username and fhp_permit(['superadmin'])==0:
			return render_template('error.html',messeg="Không chỉnh sửa được Tag/Contest của "+data.user)
		groups=[]
		for g in Groups.query.all():
			groups.append({"id":g.id,"gname":g.gname})
			if g.id==data.limit: groups[0],groups[-1]=groups[-1],groups[0]
		for i in range(1,len(groups),1):
			if groups[i-1]['gname']=='--tất cả--' and data.limit!=groups[i-1]['id']: 
				groups[i-1],groups[i]=groups[i],groups[i-1]
		for i,idp in enumerate(data.post_id.all()):
			p=Post.query.filter_by(id=idp.id_post).first()
			if p is None: continue
			tp=Tag_post.query.filter(Tag_post.id_tag==data.id,Tag_post.id_post==p.id).first()
			tmp={'id':p.id,'idp':p.id_p,'name':p.id_name,'point':tp.point,'no':tp.no,'maxsub':tp.maxsub,'tpid':tp.id}
			if tmp['no'] is None: 
				tmp['no']=i+1
				tp.no=i+1
			if tmp['maxsub'] is None: tmp['maxsub']=1
			if tmp['point'] is None: tmp['point']=10
			
			listpr.append(tmp)
		db.session.commit()
		listpr=sorted(listpr, key=lambda d: d['no'])
		for i in range(len(listpr)):
			tp=Tag_post.query.filter_by(id=listpr[i]['tpid']).first()
			tp.no=i+1
			listpr[i]['no']=i+1
			db.session.commit()
		listpr.insert(0,{'id':None,'idp':None,'name':None,'point':10,'no':0,'maxsub':5}) 
	else:
		data=Tags(tagname="",ts=datetime.now(),te=datetime.now())
	allpost=Post.query.filter((Post.user_id==current_user.id)|(Post.public==True)).order_by(Post.id_p).all()
	return render_template('admin_ql_tags.html',data=data,groups=groups,listpr=listpr,allpost=allpost)
@app.route("/admin_tagpost",methods=['GET', 'POST'])
@login_required
def admin_tagpost():
	
	if fhp_permit(['admin','superadmin'])==0: return "bạn không có quyền làm việc này"
	if request.method == 'POST':
		tagid=request.form['tagid']
		pid=request.form['postid']
		tp=Tag_post.query.filter(Tag_post.id_tag==tagid,Tag_post.id_post==pid).first()
		if tp is not None:
			tp.point=request.form['point']
			tp.no=float(request.form['no'])
			tp.maxsub=request.form['maxsub']
		else:
			tp=Tag_post(id_tag=tagid,id_post=pid,point=request.form['point'],no=float(request.form['no']),maxsub=request.form['maxsub'])
			db.session.add(tp)
		db.session.commit()
		
		tag=Tags.query.filter_by(id=tagid).first()
		post=Post.query.filter_by(id=pid).first()

		# fn="app/static/rankingc/"+tag.tagname+".txt"
		# if not os.path.isfile(fn):
		# 	f=open(fn,"w",encoding="utf-8")
		# 	f.write("[]\n{}\n{}")
		# 	f.close()
		# f=open(fn,"r",encoding="utf-8")
		# tpost=eval(f.readline())
		# tpost.append([tp.no,post.id_p])
		# for i in range(len(tpost)):
		# 	if tpost[i][0] is None: tpost[i][0]=0
		# tpost=sorted(tpost, key=lambda x: x[0])

		# tuser=eval(f.readline())
		# tdata=eval(f.readline())
		# f.close()
		
		# for user_ in tuser:
		# 	for sb in Submitcode.query.filter(Submitcode.problem==post.id, Submitcode.user==user_,Submitcode.timesb<=tag.te).all():
		# 		if sb.numtest is None: continue
		# 		if tp.point is None: tag_id.point=10
		# 		if post.testcase.count()==0: continue
		# 		point=round(sb.numtest/post.testcase.count()*tp.point,2)
		# 		if post.id_p not in tdata[user_]: 
		# 			tdata[user_][post.id_p]=[point,1,sb.numtest==post.testcase.count()]
		# 		else:
		# 			tdata[user_][post.id_p][0]=max(tdata[user_][post.id_p][0],point)
		# 			tdata[user_][post.id_p][1]+=1
		# 		tdata[user_][post.id_p][2]=max(sb.numtest==post.testcase.count(),tdata[user_][post.id_p][2])
		# f=open(fn,"w",encoding="utf-8")
		# f.write(str(tpost)+"\n")
		# f.write(str(tuser)+"\n")
		# f.write(str(tdata))
		# f.close()
	return redirect (url_for('admin_ql_tags',tagname=Tags.query.filter_by(id=tagid).first().tagname))
@app.route("/phanloaibt/")#Phân loại bài tập theo tags
def phanloaibt():
	
	session['meta']['title']="Phân loại bài tập - hpcode.edu.vn"
	data=[]
	tags=Tags.query.filter(Tags.ts==Tags.te).order_by(Tags.tagname).all()#
	for t in tags:
		tmp={}
		tmp["tagname"]=t.tagname
		tmp["tagtitle"]=t.tagtitle
		tmp["taglink"]=t.taglink
		tmp["soluong"]=Tag_post.query.filter_by(id_tag=t.id).count()
		tmp["id"]=t.id
		tmp["linkview"]=""
		if t.taglink.lower()!="none":tmp["linkview"]="Link"
		data.append(tmp)
	return render_template('phanloaibt.html',data=data)
@app.route("/listcontest/")#Phân loại bài tập thep tags
def listcontest():
	
	page = request.args.get('page', 1, type=int)
	tags=Tags.query.filter(Tags.ts!=Tags.te, Tags.te<datetime.now()).order_by(Tags.id.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'])
	lastpage=tags.pages
	tags=tags.items
	tmptags=Tags.query.filter(Tags.ts!=Tags.te, Tags.te>=datetime.now()).order_by(Tags.id.desc()).paginate().items
	data=[[],[],[]]
	for i,tag in enumerate(tags+tmptags):
		tmp={}
		tmp["title"]=tag.tagtitle
		tmp["soluong"]=Tag_post.query.filter_by(id_tag=tag.id).count()
		tmp["id"]=tag.id
		tmp["tagname"]=tag.tagname
		tmp["author"]=tag.user
		tmp['sltg']=0 # #Số lượng người tham gia
		gr=Groups.query.filter_by(id=tag.limit).first()
		if gr is not None:  tmp['sltg'] = gr.user.count()
		tmp['ts']=tag.ts #Thời gian bắt đầu
		tmp['te']=tag.te #Thời gian kết thúc Contest
		check,tmp['length']=checkTimeInOnline(tag.ts,tag.te)
		if ',' in tmp['length']: tmp['length']=tmp['length'].split(',')[0]+"<br>"+tmp['length'].split(',')[1]
		
		x=0
		if check<0: x=1
		if check>0: x=2
		data[x].append(tmp)
	
	session['meta']['title']="Danh sách kì thi - hpcode.edu.vn"
	return render_template('listcontest.html',data=data,now=getTimeNow(),page=page, lastpage=lastpage)
@app.route("/yeucaugr/",methods=['GET', 'POST'])
@app.route("/yeucaugr/<int:idgr>",methods=['GET', 'POST'])
@login_required
def yeucaugr(idgr=None):
	
	iduser=current_user.id
	grname=Groups.query.filter_by(id=idgr).first()
	if idgr is not None and grname is not None:
		grname="<b>"+grname.gname+"</b>"
		yc=Ycgr.query.filter(Ycgr.user_id==iduser,Ycgr.group_id==idgr).first()
		if yc is None:
			gr=Ycgr(user_id=iduser,group_id=idgr,status="đang chờ")
			db.session.add(gr)
			db.session.commit()
			messeg="Yêu cầu tham gia Groups "+grname+" đã được gửi"
			return render_template("error.html",messeg=messeg,data=None)
		else:
			messeg="Yêu cầu tham gia "+grname+" đang ở trạng thái <b>"+yc.status+"</b>. <br>Yêu cầu đã được gửi lại!"
			yc.status="đang chờ"
			db.session.commit()
			return render_template("error.html",messeg=messeg,data=None)
	return render_template("error.html",messeg="Có lỗi",data=None)

@app.route("/f5data")#Xóa hết các bản ghi thừa trong Database
@login_required
def f5data():
	
	if fhp_permit(['admin'])==0: return "bạn không có quyền làm việc này"
	countsb,countgu,counttp=0,0,0
	for sb in Submitcode.query.all():
		user=User.query.filter_by(username=sb.user).first()
		post =Post.query.filter_by(id=sb.problem).first()
		if user is None or post is None:
			db.session.delete(sb)
			countsb+=1
	for gu in Groupuser.query.all():
		gr  =Groups.query.filter_by(id=gu.group_id).first()
		user=User.query.filter_by(id=gu.user_id).first()
		if gr is None or user is None:
			db.session.delete(gu)
			countgu+=1
	for tp in Tag_post.query.all():
		tag  =Tags.query.filter_by(id=tp.id_tag).first()
		post =Post.query.filter_by(id=tp.id_tag).first()
		if tag is None or post is None:
			db.session.delete(tp)
			counttp+=1
	db.session.commit()	
	return 'countsb: '+str(countsb)+'. countgu: '+str(countgu)+'. counttp: '+str(counttp)
# cộng điểm và thời gian cho User
@app.route("/addmark/",methods=['GET', 'POST']) #Thêm/xóa lượt xem cho user
@login_required
def addmark():
	if fhp_permit(['superadmin'])==0: return "bạn không có quyền làm việc này"
	status = ""
	if request.method == 'POST':
		usernamethu =  request.form['username']
		addtimehoa = request.form['addtime']
		addmarkchau = request.form['addmark']
		user=User.query.filter_by(username=usernamethu).first()
		if user is None: 
			status = "<span class='text-danger'>Tài khoản không tồn tại</span>"
		else:
			user.ndow+=int(addmarkchau)
			user.thoihan=user.thoihan + timedelta(days=int(addtimehoa))
			status = "<span class='text-success'>Đã cộng điểm và thời gian cho "+usernamethu+"</span>"
		db.session.commit()
	return render_template("addmark.html",status=status)

@app.route("/delalltc/",methods=['GET', 'POST'])
@login_required
def delalltc():
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	idp= request.args.get('idp')
	post=Post.query.filter_by(id_p=idp).first()
	for tc in post.testcase.all(): db.session.delete(tc)
	db.session.commit()
	prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else "0-9"
	ffolder = "C:/Alltest/"+prefix+"/"+post.id_p
	try:
		shutil.rmtree(ffolder)
	except: print("errr")
	return redirect (url_for('upload',idp=post.id_p))

@app.route("/upload/",methods=['GET', 'POST'])
@login_required
def upload():
	
	if fhp_permit(['superadmin','admin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	status= None
	if request.method == 'POST':
		files = request.files.getlist('file[]')
		status=""
		for file in files:
			if "." not in file.filename: continue
			filename = secure_filename(file.filename).lower()
			linkt=os.path.join("app/static/chambai/tmp",filename)

			idp=filename.split(".")[0].lower().replace("_sol","")
			post=Post.query.filter_by(id_p=idp).first()
			if post is None: continue

			if filename[-3:].lower()=="zip":
				prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else '0-9'
				frootx= app.config['TESTCASE']+prefix
				if not os.path.exists(frootx): os.makedirs(frootx)
				linkt = frootx+"/"+filename
				file.save(linkt)
				status=status+filename+" "
				with ZipFile(linkt, 'r') as zip:
					for fn in zip.namelist():
						if idp+".inp" in fn : 
							snumtc = fn.replace(idp+".inp","")[:-1]
							snumtc = snumtc.replace(idp,"")[1:]
							tc=Testcase(fnstt=snumtc,post_id=post.id)
							db.session.add(tc)
							db.session.commit()	
			if filename[-4:].lower()=="docx":
				file.save(linkt)
				status=status+filename+" "
				f=open(linkt,"rb")
				if post.id_p+"_sol.docx"==filename: 
					post.sol=f.read()
					print("Đã lưu file docx cho bài tập "+post.id_p+" "+filename)
					f.close()
					db.session.commit()
				if post.id_p+".docx"==filename: 
					post.docx=f.read()
					post.body = docx2html(linkt,post.id_p) #chuyển đổi từ docx sang html
					f.close()
					db.session.commit()
			if filename[-4:].lower()==".pdf":
				file.save(linkt)
				status=status+filename+" "
				f=open(linkt,"rb")
				post.pdf=f.read()
				f.close()
				db.session.commit()
			if filename[-4:].lower() in [".png",".jpg"]:
				fn = 'app/static/chambai/tmp/'+filename
				file.save(fn)
				with open(fn, "rb") as image_file:
					post.imgbase64 = base64.b64encode(image_file.read()).decode(encoding='utf-8')
				db.session.commit()

		if len(files)==0: status="Chưa chọn tệp"
	idp= request.args.get('idp')
	post=Post.query.filter_by(id_p=idp).first()
	tests=[]
	for tc in post.testcase.all():
		fntest =gettestfilename(post,tc.fnstt)
		tinp,tout=get1test(fntest,tc.fnstt)
		if len(tinp)>30: tinp=tinp[:30]+"..."
		if len(tout)>30: tout=tout[:30]+"..."
		tests.append({"id":tc.id,"fnstt":tc.fnstt,"inp":tinp.replace("\n","<br>"),"out":tout.replace("\n","<br>")})
	
	
	session['meta']['title']="Upload - hpcode.edu.vn"
	return render_template("upload.html",tests=tests,idp=post.id_p,status=status)

@app.route("/deltest/",methods=['GET', 'POST'])
@login_required
def deltest():
	
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	idp = request.args.get('id')	
	tc=Testcase.query.filter_by(id=idp).first()
	post=Post.query.filter_by(id=tc.post_id).first()
	db.session.delete(tc)
	db.session.commit()
	ffolder = gettestfilename(post,tc.fnstt)[:-len(post.id_p)]
	shutil.rmtree(ffolder)
	return redirect (url_for('upload',idp=post.id_p))

@app.route("/newyear2022/",methods=['GET', 'POST']) #Thêm/xóa lượt xem cho user
def newyear2022():
	return render_template("newyear2022.html")

@app.route("/getAlltests/",methods=['GET', 'POST']) #xem testcase của bài tập
@login_required
def getAlltests():
	idp  = request.args.get('idp')
	
	if request.method == 'POST':
		idp = request.form['idp']
		c_hash = request.form.get('captcha-hash')
		c_text = request.form.get('captcha-text')
		if SIMPLE_CAPTCHA.verify(c_text, c_hash)==False:
			new_captcha_dict = SIMPLE_CAPTCHA.create()
			return render_template("download.html",data=0, captcha=new_captcha_dict,idp=idp,err="Bạn nhập không đúng. Hãy nhập lại")
	else:
		new_captcha_dict = SIMPLE_CAPTCHA.create()
		return render_template("download.html",data=0, captcha=new_captcha_dict,idp=idp)
	
	post=Post.query.filter_by(id_p=idp).first()
	if post is None: return render_template("error.html",messeg="Bài tập không tồn tại")
	if len(checkPinC(post))>0 and current_user.giaovien!=1: 
		return render_template("error.html",messeg="Bài tập thuộc Contest chưa kết thúc")
	marksub=100 if current_user.giaovien!=1 else 10
	
	if(current_user.ndow<marksub): return render_template("error.html",messeg="Bạn không đủ điểm")
	#tc=post.testcase.all()
	folder_n = os.path.join("app/static/chambai/tmp/","["+current_user.username+"]["+idp+"]")
	#if not os.path.exists(folder_n): os.makedirs(folder_n)
	prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else "0-9"
	fntestpost = app.config['TESTCASE']+prefix+"/"+post.id_p+".zip" #đường dẫn file test của bài tập
	folder_n = "app/static/chambai/tmp/"+post.id_p+".zip"
	copyfile(fntestpost,folder_n)
	tmp = urlparse(request.url)
	urlx = tmp.scheme +"://"+tmp.netloc+"/"
	link=os.path.join(urlx,folder_n[4:]).replace("http://","https://")
	print(link)
	current_user.ndow=current_user.ndow-marksub
	db.session.commit()
	return render_template('download.html',link=link,data=1)

@app.route("/tct/",methods=['GET', 'POST']) #Lấy testcase của toàn bộ bài tập trong Contest
@login_required
def tct():
	
	if fhp_permit(["superadmin"])!=1:
		return render_template("error.html",messeg="Bạn không có quyền làm điều này")
	tagname  = request.args.get('tagname')
	tag = Tags.query.filter_by(tagname=tagname).first()
	if tag is None:
		return render_template("error.html",messeg="Kỳ thi không tồn tại")
	for pid in tag.post_id.all():
		post=Post.query.filter_by(id=pid.id_post).first()
		if post is None: continue
		print(post.id_p)
		prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else "0-9"
		fns = "C:/Alltest/"+prefix+"/"+post.id_p
		shutil.copytree(fns,"app/static/download/"+post.id_p)

		link="app/static/download/"+post.id_p
		#lấy đề thi docx

		if post.docx is not None:
			f=open(link+".docx","wb")
			f.write(post.docx)
			f.close()
		if post.pdf is not None:
			f=open(link+".pdf","wb")
			f.write(post.pdf)
			f.close()
		if post.sol is not None:
			f=open(link+"_sol.docx","wb")
			f.write(post.sol)
			f.close()
	return "Done"

@app.route("/directlink/",methods=['GET', 'POST']) #Chuyển hướng đến link

def directlink():
	link  = request.args.get('link')
	arg1 = request.args.get('arg1')
	#idcaptcha = request.args.get('idcaptcha')
	
	fcheck = "app/static/chambai/tmp/"+link+"_"+str(arg1)+".txt"
	
	if not os.path.isfile(fcheck): f=open(fcheck,"w"); f.close()
	

	tmp = urlparse(request.url)
	urlx = tmp.scheme +"://"+tmp.netloc + "/"+link
	timeleft = 30
	
	if link == "gettests": 
		urlx = urlx +"/?id="+arg1
		note = "Chuyển hướng đến Testcase sau "
	elif link=="xemde":
		urlx = urlx +"/?idde="+arg1
		note = "Chuyển hướng đến Đề thi sau "
		timeleft = 15
	elif link=="viewlog":
		urlx = urlx +"/"+arg1
		note = "Chuyển hướng đến file log sau "
		timeleft = 10
	elif link=="getdocx":
		urlx = urlx +"/?idp="+arg1
		note = "Chuyển hướng đến Đề thi (docx) sau "
		timeleft = 30
	elif link=="solution":
		urlx = urlx +"/?idp="+arg1
		note = "Chuyển hướng đến Hướng dẫn (docx) sau "
		timeleft = 30
	elif link=="getAlltests":
		urlx = urlx +"/?idp="+arg1
		note = "Chuyển hướng đến trang tải Tests sau "
		timeleft = 60
	else:
		return render_template("error.html",messeg="Chuyển hướng đến link không hợp lệ")
	if fhp_permit(["admin"]): timeleft = 5
	return render_template("directlink.html",link=urlx,timeleft=timeleft,note=note)
@app.route("/gettests/",methods=['GET', 'POST']) #xem testcase của bài tập
@login_required
def gettests():
	#deletefilecode('app/static/hpcaptchar')
	idt  = request.args.get('id')#id của testcase
	if idt is not None: idt=int(idt)
	if request.method == 'POST':
		idt = int(request.form['idt'])
		c_hash = request.form.get('captcha-hash')
		c_text = request.form.get('captcha-text')
		if SIMPLE_CAPTCHA.verify(c_text, c_hash)==False:
			new_captcha_dict = SIMPLE_CAPTCHA.create()
			return render_template("gettests.html",data=0, captcha=new_captcha_dict,idt=idt,err="Bạn nhập không đúng. Hãy nhập lại")
	else:
		new_captcha_dict = SIMPLE_CAPTCHA.create()
		return render_template("gettests.html",data=0, captcha=new_captcha_dict,idt=idt)	

	tc=Testcase.query.filter_by(id=idt).first()
	if tc is None: return render_template("error.html",messeg="Có lỗi")
	post=Post.query.filter_by(id=tc.post_id).first()
	

	if post is None: return render_template("error.html",messeg="Có lỗi")
	session['meta']['title']=post.id_name+" - hpcode.edu.vn"
	# if len(checkPinC(post))>0 and fhp_permit(["admin","superadmin","freetest"])!=1: 
	# 	return render_template("error.html",messeg="Bài tập thuộc Contest chưa kết thúc")

	mark,numdow=2,numview_testcase()
	countx= current_user.testid.filter(User_tests.time>datetime.now() - timedelta(days=1)).count()
	if countx<numdow: 
		mark=0 #nếu lượt tải miễn phí vẫn còn thì không cần điểm
	# elif len(checkPinC(post))>0 and fhp_permit(["admin","superadmin","freetest"])!=1: #neu luot tai mien phi ko con thi ko duoc tai bai khi Contest dien ra
	# 	return render_template("error.html",messeg="Bài tập thuộc Contest chưa kết thúc")
	usert = User_tests.query.filter(User_tests.userid==current_user.id,User_tests.testid==idt).first()
	if usert is not None: mark=0 #nếu user đã tải test ít nhất 1 lần trước đó thì không trừ điểm

	if current_user.ndow<mark: return render_template("error.html",messeg="Bạn không có điểm để xem testcase")
	current_user.ndow-=mark
	if usert is None: #Nếu user chưa tải lần nào thì ghi nhận lượt tải
		ut = User_tests(userid=current_user.id,testid=idt)
		db.session.add(ut)
	#Cập nhật thêm lượt them cho testcase (testcase có thêm một lượt xem)
	if tc.numview is None: tc.numview=0
	tc.numview +=1
	db.session.commit()	
	fntest =gettestfilename(post,tc.fnstt)
	inp,out=get1test(fntest,tc.fnstt)
	fdload = "app/static/download/"+tc.fnstt+"_"+post.id_p
	f = open(fdload+".inp","w")
	f.write(inp)
	f.close()
	f = open(fdload+".out","w")
	f.write(inp)
	f.close()
	
	data={"idp":post.id_name,'inp':inp,'out':out,"link":[],"ndownless":""} #ndownless: Lượt tải miễn phí còn lại
	
	data['ndownless']="Bạn còn <b> <span class='text-success'>" + str(max(0,numdow-countx-1)) +" </span> </b>lượt tải miễn phí"
	data['link']=[app.config['DOMAIN']+fdload[4:]+".inp",app.config['DOMAIN']+fdload[4:]+".out"]
	
	data['inp']=data['inp'].replace("\n","<br>")	
	data['out']=data['out'].replace("\n","<br>")
	lenmax = 150
	if len(data['inp'])>lenmax: data['inp']=data['inp'][:lenmax]+"<br>...<br><span class='text-success'>Tải về để xem toàn bộ test</span>"
	if len(data['out'])>lenmax: data['out']=data['out'][:lenmax]+"<br>...<br><span class='text-success'>Tải về để xem toàn bộ test</span>"
	return render_template("gettests.html",data=data)
#"render_template("download.html",link=app.config['DOMAIN']+fn[4:])
@app.route("/uptests/",methods=['GET', 'POST']) 
@login_required
def uptests():
	
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	for post in Post.query.all():
		alltest = post.testcase.all()
		linkt="app/static/chambai/test/"
		if post.id_p[0]<='9' and post.id_p[0]>='0': 
			linkt=linkt+"0-9"
		else:
			linkt=linkt+post.id_p[0]
		linkt=linkt+"/"+post.id_p+".zip"
		if not os.path.isfile(linkt): linkt=None
		if linkt is not None and len(alltest)==0:
			with ZipFile(linkt, 'r') as zip:
				for fn in zip.namelist():
					if "input" not in fn or ".txt" not in fn: continue
					inp=zip.read(fn)
					out=zip.read(fn.replace('input','output'))
					tc=Testcase(inp=inp,out=out,post_id=post.id)
					db.session.add(tc)
	db.session.commit()
	return "done"

@app.route("/rejuger/",methods=['GET', 'POST']) 
@login_required
def rejuger():
	
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	idp = request.args.get('idp')
	post=Post.query.filter_by(id_p=idp).first()
	if post is None: return render_template("error.html",messeg="Bài tập không có")
	for sb in Submitcode.query.filter_by(problem=post.id).all(): sb.graded=2
	db.session.commit()
	return redirect (url_for('viewctpr',idp=idp))
@app.route("/addgv/",methods=['GET', 'POST']) #Thêm giáo viên vào danh sách
@login_required
def addgv():
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	status = None
	data = []
	if request.method == 'POST':
		username = request.form['username']
		sl = request.form['sl']
		user = User.query.filter_by(username=username).first()
		if user is None:
			status = "<span class='text-danger'>Tài khoản không tồn tại</span>"
		else:
			user.giaovien = 1
			user.slhocsinh = int(sl)
			db.session.commit()
			status = "<span class='text-success'>Đã thêm giáo viên "+username+"</span>"
	for user in User.query.filter(User.giaovien==1).order_by(User.username).all():
		slthucte = Giaovienhs.query.filter_by(gv_id=user.id).count()
		tmp = {}
		tmp['username'] = user.username
		tmp['fullname'] = user.fullname
		tmp['sl'] = str(slthucte)+"/"+str(user.slhocsinh)
		data.append(tmp)	
	return render_template("addgv.html",status = status,data=data)
@app.route("/delhs/",methods=['GET', 'POST']) #Thêm giáo viên vào danh sách
@login_required
def delhs():
	username = request.args.get('id')
	hs = User.query.filter_by(username=username).first()
	gvhs = Giaovienhs.query.filter_by(hs_id=hs.id,gv_id=current_user.id).first()
	if gvhs is None: return render_template("error.html",messeg="Học sinh không thuộc giáo viên này")
	db.session.delete(gvhs)
	hs.thoihan = datetime.now()#Thời hạn của học sinh là 0
	db.session.commit()
	return redirect (url_for('giaovien'))
@app.route("/resetpasshs/",methods=['GET', 'POST']) #Thêm giáo viên vào danh sách
@login_required
def resetpasshs():
	username = request.args.get('id')
	hs = User.query.filter_by(username=username).first()
	gvhs = Giaovienhs.query.filter_by(hs_id=hs.id,gv_id=current_user.id).first()
	if gvhs is None: return render_template("error.html",messeg="Học sinh không thuộc giáo viên này")
	hs.set_password('haiphongoj')
	db.session.commit()
	return redirect (url_for('giaovien'))

@app.route("/delgv/",methods=['GET', 'POST']) #Thêm giáo viên vào danh sách
@login_required
def delgv():
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	username = request.args.get('id')
	user = User.query.filter_by(username=username).first()
	user.giaovien = 0
	user.slhocsinh = 0
	db.session.commit()
	return redirect (url_for('addgv'))

@app.route("/hp/",methods=['GET', 'POST']) 
@login_required
def hp():
	
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	for tg in Tags.query.all():
		tg.ts=conertTimeHTMLtoPython(tg.timeb)
		tg.te=conertTimeHTMLtoPython(tg.timee)
	db.session.commit()
	return "done"

@app.route("/video/",methods=['GET', 'POST']) 
def video():
	
	lop = request.args.get('lop')
	if lop is None: lop="tinhoc"
	#if lop=="tinhoc": return redirect (url_for('vtinhoc'))
	data={}
	keyfirst,datav=None,None
	for d in Videohp.query.filter_by(lop=lop).all():
		tmpdata= {"idgd":"","idv":d.idv,"title":d.title,"sach":d.sach,"ytber":d.author,"mon":d.mon,"views":d.views,'num':d.id if d.num is None else int(d.num)}
		if d.idgd is not None: tmpdata['idgd'] = d.idgd
		if d.views is None: tmpdata['views']=""
		key=no_accent_vietnamese(d.author+d.sach+d.mon).replace("-","").lower().replace("&","")
		if keyfirst is None: keyfirst=key
		if key not in data: data[key]=[]
		data[key].append(tmpdata)
		if datav is None: datav=tmpdata #Thông tin Video đang phát
	if Videohp.query.filter_by(lop=lop).count()==0:
		return render_template("error.html",messeg="Chưa có Video")
	db.session.commit()
	for key in data: data[key] = sorted(data[key], key=lambda d: d['num']) 
	return render_template("video.html",data=data,datav=datav,keyfirst=keyfirst)

@app.route("/editv/",methods=['GET', 'POST']) 
@login_required
def editv():
	
	data={}
	data['sach']={'10 Vạn câu hỏi vì sao':'10 Vạn câu hỏi vì sao',"":"Khác",'CD':'Cánh diều',"KNTT&CS":"Kết nối tri thức với cuộc sống","CTST":"Chân trời sáng tạo","Story English":"Story English"}
	data['lop']={'0':'Mẫu giáo','tinhoc':'Tin học','khampha':'Khám phá'}
	for i in range(1,13): data['lop'][str(i)]=str(i)
	data['mon']={'':'Khác','CTDL-GT':'Cấu trúc dữ liệu và Giải thuật','Python':"Python",'Cpp':'C++','Toán':'Toán','Tiếng Việt':'Tiếng Việt','English':'English','Tin học':'Tin học'}

	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	idv = request.args.get('idv')
	vid = Videohp.query.filter_by(idv=idv).first()
	status = None
	if vid is not None: 
		status = "Đang thay đổi thông tin video"
	else:
		vid=Videohp()
	if request.method == 'POST':
		idv=request.form['idvx']
		if request.form.get('delvid') is not None:
			vid = Videohp.query.filter_by(idv=idv).first()
			db.session.delete(vid)
			db.session.commit()
			return render_template("error.html",messeg="Đã xóa Video "+idv)
		status = "Đã cập nhật"
		if request.form.get('addnew') is not None:
			if Videohp.query.filter_by(idv=idv).first() is not None:
				status = "Video đã có"
			else:
				vid = Videohp(idv=idv)
				db.session.add(vid)
				db.session.commit()
				status = "Đã thêm mới"
		vid = Videohp.query.filter_by(idv=idv).first()
		if vid is not None:
			vid.title = request.form['title']
			vid.num = int(request.form['num'])
			vid.sach = request.form['sach']
			vid.lop = request.form['lop']
			vid.mon = request.form['mon']
			vid.author = request.form['author']
			vid.idgd = request.form['idgd']
			db.session.commit()

	updateinforvideo(idv)
	if vid.num is None: vid.num=vid.id
	if vid.idgd is None: vid.idgd=""
	db.session.commit()
	return render_template("editv.html",vid=vid,status=status,data=data)			

@app.route("/updateviews/",methods=['GET', 'POST']) 
@login_required
def updateviews():
	
	if fhp_permit(['superadmin'])==0: return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	f=open("app/static/videoth/idv.txt","r",encoding="utf-8"); idgd_=f.read().split("\n");f.close()
	idgd={}
	for d in idgd_[:-1]: idgd[d.split()[0][:-4]]=d.split()[1]
	Apl=[]
	Apl.append({'link':'PLFUQ0OTVjaq3RTN882buZZX0vZg_7do0P','sach':'10 Vạn câu hỏi vì sao','author':'','lop':'khampha','mon':''})
	Apl.append({"link":"PLAbgKpL3K4iQxSO-J39UougYbZeLTIBwG","sach":"KNTT&CS",'author':'Cô Thu','lop':'3','mon':'Toán'})
	Apl.append({"link":"PLAbgKpL3K4iTDx9RI4tWUjq8Eq85xDpvS","sach":"KNTT&CS",'author':'Cô Thu','lop':'3','mon':'Tiếng Việt'})
	Apl.append({"link":"PL972mDjANyAK_22fIfKATkH_kR2xkKnlE","sach":"KNTT&CS",'author':'Cô Vân','lop':'3','mon':'Toán'})
	Apl.append({"link":"PL0GVt1tuJHVQrWvsLGEIyjudRFeHvKe1j","sach":"KNTT&CS",'author':'Cô Loan','lop':'3','mon':'Toán'})
	Apl.append({"link":"PL3PyovaaQ3v7H4cbp-I9A16S2eIZh1BaR","sach":"KNTT&CS",'author':'Ms Hạnh','lop':'3','mon':'Toán'})
	Apl.append({"link":"PLAbgKpL3K4iSzEo96gwq_b75tCGldXDLN","sach":"CD",'author':'Cô Thu','lop':'3','mon':'Tiếng Việt'})
	Apl.append({"link":"PLxUdsmN71otAwasofrykEv1mjGOk2DsjH","sach":"CD",'author':'Thầy Liêm','lop':'3','mon':'Tiếng Việt'})
	Apl.append({"link":"PLii5rkhsE0Ld3xCgxG6j5fw7RlG2S5czO","sach":"Story English","author":"English Singsing",'lop':'0','mon':'English'})
	Apl.append({"link":"PLk5_KRHza8nYR18rfgzosqhTwC_G1vo9A","sach":"Family and Friends","author":"Hello Kids",'lop': '1',"mon": "English"})
	Apl.append({"link":"PLii5rkhsE0LeIi1U-PJZ2s1inRgnzjggR","sach":"Story - Simple Speaking","author":"English Singsing",'lop':'0',"mon":"English"})
	Apl.append({"link":"PLii5rkhsE0LfXbq3CnoZZNDdb8-WaQzFa","sach":"Phonics Song","author":"English Singsing",'lop':'0','mon':'English'})
	Apl.append({"link":"PLii5rkhsE0LejvVtODbfqhNs2sfk2phpn","sach":"Phonics Story","author":"English Singsing",'lop':'0','mon':'English'})
	
	cnt=0
	f=open("app/static/videoth/newvideo.txt",'w',encoding='utf-8')
	for pltmp in Apl:
		pl=Playlist("https://www.youtube.com/playlist?list="+pltmp['link'])
		for url in pl.video_urls:
			idv=url.split("=")[1]
			print(cnt,end=' ')
			vid=Videohp.query.filter_by(idv=idv).first()
			if vid is not None:
				try:
					yt=YouTube(url)
					vid.views=yt.views
					vid.descr=yt.description
				except:
					print('err 1',vid.idv)
			else:
				yt=YouTube(url)
				#ys=yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
				vid=Videohp(idv=idv)
				vid.views=yt.views
				vid.descr=yt.description
				vid.title = yt.title
				vid.mon = pltmp['mon']
				vid.author = pltmp['author']
				vid.lop = pltmp['lop']
				vid.sach = pltmp['sach']
				vid.idgd =""
				vid.num=vid.idv
				db.session.add(vid)
				cnt=cnt+1 
				f.write(idv+' '+pltmp['link']+'\n')
	f.close()
	db.session.commit()
	return render_template("error.html",messeg="Đã cập nhật lượt xem cho "+ str(cnt) + " Video")

@app.route("/solvideo/",methods=['GET', 'POST']) 
@login_required
def solvideo():
	
	session['meta']['title']="Admin - Thêm hướng dẫn cho bài tập - hpcode.edu.vn"
	if fhp_permit(['superadmin','admin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	status ="Nhập link youtube cho bài tập"
	ytlink = None
	idp=None
	if request.method == 'POST':
		idp = int(request.form['idp'])
		session['meta']['title']="Admin - Thêm hướng dẫn cho bài tập "+idp+" - hpcode.edu.vn"
		ytlink = request.form['ytlink']
		post = Post.query.filter_by(id=idp).first()
		status = "Link youtube không đúng"
		if "?v=" in ytlink:
			ytlink= ytlink.split("?v=")[1].replace("&t","?start")[:-1]
			post.yt = ytlink
			db.session.commit()
			status = "Đã thêm/cập nhập link youtube cho bài "+ post.id_p
	allpost=Post.query.filter((Post.user_id==current_user.id)|(Post.public==True)).order_by(Post.id_p).all()
	return render_template("solvideo.html",idp=idp,status=status,ytlink=ytlink,allpost=allpost)

@app.route("/getallcode/",methods=['GET', 'POST']) 
@login_required
def getallcode(): #Lấy code của một bài tập 
	
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	idp = request.args.get('idp')
	allp = [p.id for p in Post.query.all()]
	#allcode=Submitcode.query.filter_by(fulltest=1).all()
	if idp!="allcode":
		p=Post.query.filter_by(id_p=idp).first()
		if p is None: return render_template("error.html",messeg="Bài tập không tồn tại")
		allp=[p.id]
		#allcode=Submitcode.query.filter(Submitcode.fulltest==1,Submitcode.problem==p.id).all()
	rootfn="app/static/download/"
	stt=0
	for pid in allp:
		for ext in ['pas','cpp','py']:
			allcode = Submitcode.query.filter(Submitcode.fulltest==1,Submitcode.problem==pid, Submitcode.ext==ext).order_by(Submitcode.timesb.desc()).limit(10).all()
			for sb in allcode:
				idx= str(stt)
				stt+=1
				while len(idx)<5: idx='0'+idx
				pro= Post.query.filter_by(id=sb.problem).first()
				if pro is None: continue
		
				fn=rootfn+pro.id_p
				if not os.path.exists(fn): os.makedirs(fn)
				fn=fn+"/["+idx+"]["+pro.id_p+"]."+sb.ext
				f=open(fn,"w",encoding="utf-8")
				f.write(sb.code)
				f.close()
				if(sb.id%100==0): print(sb.id)
	return "done"
@app.route("/getuser/",methods=['GET', 'POST']) 
@login_required
def getuser():
	
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	user = User.query.filter_by(email="thaophuongdo0911@gmail.com").first()
	if user is None: return "None"
	return user.username

@app.route("/tmpp/",methods=['GET', 'POST']) 
@login_required
def tmpp(): #Kiểm tra lượt nộp bài có fulltest hay không?
	
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này")
	c=0
	for sb in Submitcode.query.all():
		post = Post.query.filter_by(id=sb.problem).first()
		if post is None: 
			sb.fulltest=0
			continue
		if sb.numtest == post.testcase.count():
			sb.fulltest=1
			if c%100==0: 
				print(c,sb.numtest,post.testcase.count())
			c+=1
		else: sb.fulltest=0
	db.session.commit()
	return c

@app.route("/initcontest/",methods=['GET', 'POST']) 
@login_required
def initcontest(): #Khởi tạo các Contest [hsga, hsgb,hsgthcs,thi10ct]
	
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	for cname in ["ts10", "thcs","hsga","hsgb"]:
		tag = Tags.query.filter_by(tagname=cname).first()
		if tag is None: continue
		for x in tag.post_id.all(): db.session.delete(x)
		db.session.commit()
	for madt in ["ts10","thcs","hsga","hsgb"]:
		tag = Tags.query.filter_by(tagname=madt).first()
		for dethi in Dethi.query.filter_by(makythi=madt).all():
			if dethi is None: continue
			for post in dethi.post_id.all():
				tp = Tag_post(id_post=post.id_post,id_tag=tag.id,maxsub=10)
				db.session.add(tp)
	db.session.commit()
	return "done"
@app.route("/khoatk/",methods=['GET', 'POST']) 
@login_required
def khoatk():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	if request.method == 'POST':
		username = request.form['username']
		user = User.query.filter_by(username = username).first()
		if user is None:
			return render_template("error.html",messeg="User "+username +" không tồn tại")
		if user.khoatk==0: user.khoatk=1 #Khóa tài khoản
		else: user.khoatk=0 #Mở khóa tài khoản
		db.session.commit()
		return redirect('/info/'+username) #render_template("error.html",messeg="Tài khoản "+username +" đã bị khóa")
	return "done"

@app.route("/xacthuc/",methods=['GET', 'POST']) 
@login_required
def xacthuc():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	if request.method == 'POST':
		username = request.form['username']
		user = User.query.filter_by(username = username).first()
		if user is None:
			return render_template("error.html",messeg="User "+username +" không tồn tại")
		if user.xacthuc in [0,None]: user.xacthuc=1 
		db.session.commit()
		return redirect('/info/'+username) #render_template("error.html",messeg="Tài khoản "+username +" đã bị khóa")
	return "done"

@app.route("/updateshortlink/",methods=['GET', 'POST']) 
@login_required
def updateshortlink():
	
	if request.method == 'POST':
		key = request.form['shortlink']
		title = request.form['title']
		timewait = request.form['timewait']
		shortlink = Shortlink.query.filter_by(key=key).first()
		if shortlink is not None:
			shortlink.title = title
			shortlink.timewait = timewait
			db.session.commit()
	return redirect('/shortlink/')

@app.route("/hplink/",methods=['GET', 'POST']) 
def hplink():
	session['meta']["title"]="hpcode.edu.vn - Rút gọn link"
	datalink=[]
	for link in Shortlink.query.order_by(Shortlink.timeb.desc()).limit(50).all():
		titlelink = link.title if ".zip" not in link.title else "<b>Bộ test bài <a href='https://hpcode.edu.vn/viewctpr/?idp="+link.title.split('.')[0]+"'>"+link.title.split('.')[0]+"</a></b>"
		username = User.query.filter_by(id=link.user_id).first().username
		datalink.append({'title':titlelink,'shortlink':link.key,'sl':link.sl,'timewait':link.timewait,'user':username})
	datatoplink=[]
	for link in Shortlink.query.order_by(Shortlink.sl.desc()).limit(50).all():
		username = User.query.filter_by(id=link.user_id).first().username
		titlelink = link.title if ".zip" not in link.title else "<b>Bộ test bài <a href='https://hpcode.edu.vn/viewctpr/?idp="+link.title.split('.')[0]+"'>"+link.title.split('.')[0]+"<b></a>"
		datatoplink.append({'title':titlelink,'shortlink':link.key,'sl':link.sl,'timewait':link.timewait,'user':username})
	return render_template("hplink.html",datatoplink=datatoplink,datalink=datalink,domain=app.config['DOMAIN'])
@app.route("/shortlink/",methods=['GET', 'POST']) 
@login_required
def shortlink():
	datalink=[]
	countviewlink = 0
	for link in Shortlink.query.filter_by(user_id=current_user.id).order_by(Shortlink.timeb.desc()).all():
		datalink.append({'title':link.title,'shortlink':link.key,'sl':link.sl,'timewait':link.timewait,"slink":link.stl})
		countviewlink+=link.sl
	status = None
	data = {'link':'',"shortlink":"","title":"",'domain':app.config['DOMAIN'],'timewait':30,'countviewlink':countviewlink}
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	if request.method == 'POST':
		data['link'] = request.form['link']
		data['title'] = request.form['title']
		data['shortlink'] = request.form['shortlink']
		data['timewait'] = request.form['timewait']
		if "http" not in data['link']:
			status = "<span class='text-danger'><b>Link không hợp lệ</b></span>"
			return render_template("shortlink.html",status=status,data=data,check=0,datalink=datalink)
		if data['shortlink'] in app.config['ALLOW_ROUTE'] and len(data['shortlink'])>0:
			status = "<span class='text-danger'>Không được phép sử dụng mã rút gọn: <b>"+data['shortlink']+"</b></span>"
			return render_template("shortlink.html",status=status,data=data,check=0,datalink=datalink)
		if len(data['shortlink'])==0:
			while 1==1:
				data['shortlink'] = ''.join(random.choices(string.ascii_letters+string.digits,k=5))
				sl = Shortlink.query.filter_by(key=data['shortlink']).first()
				if sl is None: break
		else:
			for c in data['shortlink']:
				if c not in app.config['ALLCHAR']: 
					status = "<span class='text-danger'><b>Lỗi: Chỉ được sử dụng ký tự chữ cái và số</b></span>"
					return render_template("shortlink.html",status=status,data=data,check=0,datalink=datalink)
			sl = Shortlink.query.filter_by(key=data['shortlink']).first()
			if sl is not None:
				status = "<span class='text-danger'><b>Lỗi: Mã rút gọn đã có</b></span>"
				return render_template("shortlink.html",status=status,data=data,check=0,datalink=datalink)
		
		sl = Shortlink(key=data['shortlink'],user_id=current_user.id,link=data['link'],title=data['title'],timewait=data['timewait'])
		db.session.add(sl)
		db.session.commit()
		status = "<span class='text-success'><b>Rút gọn thành công</b></span>"
		datalink.insert(0,{'title':sl.title,'shortlink':sl.key,'sl':sl.sl,'timewait':sl.timewait})
		#data['shortlink'] = ""
		return render_template("shortlink.html",status=status,data=data,check=1,datalink=datalink)
	return render_template("shortlink.html",status=None,data=data,check=0,datalink=datalink)

@app.route("/loaitkkhoinhom/",methods=['GET', 'POST']) 
@login_required
def loaitkkhoinhom():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	for user in User.query.filter_by(khoatk=1).all():
		for gr in Groups.query.all():
			gu = Groupuser.query.filter(Groupuser.group_id==gr.id,Groupuser.user_id==user.id).first()
			if gu is not None:
				db.session.delete(gu)
	db.session.commit()
	return render_template("error.html",messeg="Đã xóa hết các User bị khóa khỏi tất cả các Groups") 

@app.route("/userdiemcao/",methods=['GET', 'POST']) 
@login_required
def userdiemcao():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	note = ""
	for user in User.query.filter(User.ndow>=1000).all():
		note= note +user.username+": "+str(user.ndow)+"<br>"
	#db.session.commit()
	note = "<b>Chưa có file word</b><br>"
	c = 0
	for post in Post.query.all():
		if post.docx is None:
			note = note + post.id_name +": "+ post.id_p + "<br>"
			c+=1
		if c>20: break
	c = 0
	note = note + "<br><hr><b>Chưa có hướng dẫn:</b><br>"		
	for post in Post.query.limit(20).all():
		if post.sol is None:
			note = note + post.id_name +": "+ post.id_p + "<br>"
			c+=1
		if c>20: break
	return render_template("error.html",messeg=note) 

@app.route("/giaiqg/",methods=['GET', 'POST']) 
def giaiqg():
	return render_template("giaiqg.html") 

@app.route("/downloadalltest/",methods=['GET', 'POST']) 
@login_required
def downloadalltest():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	root= "C://Alltest"
	if not os.path.isdir(root): os.mkdir(root)
	cnt=1
	for p in Post.query.all():
		print(cnt,p.id_p)
		pre = p.id_p[0]
		#if pre!='s': continue
		if pre in ['0','1','2','3','4','5','6','7','8','9']: pre = '0-9'
		fn = os.path.join(root,pre)
		if not os.path.isdir(fn): os.mkdir(fn)
		fn = os.path.join(fn,p.id_p)
		if not os.path.isdir(fn): os.mkdir(fn)
		numtc=0
		for t in p.testcase.all():
			st = str(numtc)
			if len(st)==1: st='0'+st
			st="test"+st
			t.fnstt = st
			numtc+=1
			fntest = os.path.join(fn,st)
			if not os.path.isdir(fntest): os.mkdir(fntest)
			f=open(os.path.join(fntest,p.id_p+".inp"),"w",encoding='utf-8')
			f.write(t.inp.decode().replace("\n\n","\n"))
			f.close()
			f=open(os.path.join(fntest,p.id_p+".out"),"w",encoding='utf-8')
			f.write(t.out.decode().replace("\n\n","\n"))
			f.close()
		cnt+=1
	db.session.commit()
	return "done"

@app.route("/hpx/",methods=['GET', 'POST']) 
@login_required
def hpx():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	for post in Post.query.all():
		#if post.docx is None: continue
		fndocx = "app/static/chambai/tmp/"+post.id_p+".docx"
		print(post.id_p)
		if post.docx is not None:
			f=open(fndocx,"wb")
			f.write(post.docx)
			f.close()
		else:
			continue
		 
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
			html = html.replace("media/image"+si+".png","../static/hinhanh/problem/"+post.id_p+si+".jpg")
		post.body= html#.encode('utf-8')
	db.session.commit()	
	return "done"
@app.route("/cp/",methods=['GET', 'POST']) 
@login_required
def cp():
	if fhp_permit(['superadmin'])==0: 
		return render_template("error.html",messeg="Bạn không có quyền làm việc này") 
	current_user.thoihan=current_user.thoihan + timedelta(days=100)
	# for user in User.query.filter_by(xacthuc=1).all():
	# 	user.khoatk=0
	# 	user.thoihan = max(user.thoihan if user.thoihan is not None else datetime.now(),datetime.now())+timedelta(days=100)

	db.session.commit()
	
	return "done"
	fn50 = "app/static/hinhanh/QRcode_nhanTien/50.jpg"
	fn99 = "app/static/hinhanh/QRcode_nhanTien/99.jpg"
	fn149 = "app/static/hinhanh/QRcode_nhanTien/149.jpg"
	with open(fn50, "rb") as image_file:
		x = base64.b64encode(image_file.read()).decode(encoding='utf-8')
		data = Imagebase64(base64=x,loai="Nhận tiền",ma="50",ghichu="50K")
		db.session.add(data)
	with open(fn99, "rb") as image_file:
		x = base64.b64encode(image_file.read()).decode(encoding='utf-8')
		data = Imagebase64(base64=x,loai="Nhận tiền",ma="99",ghichu="99K")
		db.session.add(data)
	with open(fn149, "rb") as image_file:
		x = base64.b64encode(image_file.read()).decode(encoding='utf-8')
		data = Imagebase64(base64=x,loai="Nhận tiền",ma="149",ghichu="149K")
		db.session.add(data)
	db.session.commit()
	return "done"