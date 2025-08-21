import os, subprocess, time, psutil, datetime
import sqlite3
from zipfile import ZipFile
import pathlib
import concurrent.futures as futures
import random
from docx2pdf import convert
def timeout(timelimit):
    def decorator(func):
        def decorated(*args, **kwargs):
            with futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timelimit)
                except futures.TimeoutError:
                    print('Timedout!')
                    #raise TimeoutError from None
                    
                # else:
                #     print(result)
                
                executor._threads.clear()
                
                futures.thread._threads_queues.clear()
                
                return result
        return decorated
    return decorator
def deletefilecode():
	folder='tmp'
	for fn in os.listdir(folder):
		if os.path.isdir(os.path.join(folder,fn)):continue
		fname = pathlib.Path(os.path.join(folder,fn))
		subtime=datetime.datetime.now()-datetime.datetime.fromtimestamp(fname.stat().st_mtime)
		second=subtime.total_seconds()
		tminis=30 if ".log" in fn else 0.1
		if ".zip" in fn: tminis=10
		if second>tminis*60: 
			try:
				os.remove( os.path.join(folder,fn))
				print("removed",os.path.join(folder,fn))
			except:
				print('cant delete file',fn)
				for p in psutil.process_iter():
					if fn[:-4] in p.name():	p.kill()
def c1(st): #Xử lý cho trình chấm C1: So sánh hai từ giống nhau theo đúng thứ tự xuất hiện. Có hai dấu cách liên tiếp,
			#hoặc có dòng trống ở đầu, cuối không ảnh hưởng đến kết quả
	char=['\r\n','\n','\t','  ']
	for c in char: st=st.replace(c,' ')
	while '  ' in st: st=st.replace('  ',' ')
	if len(st)>0 and st[0] ==' ': st=st[1:]
	if len(st)>0 and st[-1]==' ': st=st[:-1]
	return st
def createlog(flog,st,flag=None):#ghi mới hoặc ghi vào cuối (flag=None) tệp hoặc đầu tệp (flag=0)
	st=st.replace("tmp",str(random.randint(1,1000))).replace("[","")
	if flag is None:
		f=open(flog,'a',encoding='utf-8')
	elif flag==1:#ghi vào đầu tệp
		f=open(flog,'r+',encoding='utf-8')
		f.seek(0)
	elif flag==0: #ghi mới
		f=open(flog,'w',encoding='utf-8')
	f.write(st)
	f.close()
def trinhcham_c1(out,ans): #Không phân biệt HOA/thường
	out=c1(out).lower()
	ans=c1(ans).lower()
	if out==ans: return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
def trinhcham_c2(out,ans): #Như trình chấm C1 nhưng PHÂN BIỆT HOA/thường
	out=c1(out)
	ans=c1(ans)
	if out==ans: return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
def trinhcham_c3(out,ans,e=None):  # So khớp các từ theo đúng thứ tự, nếu hai từ là xâu thì phải giống nhau hoàn toàn
							  # Nếu hai từ là số thực thì có độ lệch nhỏ hơn e (mặc định 1e-5)
							  # Việc thừa các dòng đầu tiên, dòng cuối cùng và ký tự trắng không ảnh hưởng đến kết quả
	out=c1(out).split(' ')
	ans=c1(ans).split(' ')
	if e is None: e=0.00001
	e=float(e)
	truex=0
	for i in range(min(len(out),len(ans))):
		x=out[i].replace('.','',1).isdigit()
		y=ans[i].replace('.','',1).isdigit()
		if (x and y and abs(float(x)-float(y))<=e) or (x==y):  truex=truex+1
	if truex==max(len(out),len(ans)): return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	if truex==0: return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
	return truex/max(len(out),len(ans)),"<span class='text-warning'>Đúng một phần</span>. "
def trinhcham_s1(out,ans): #So sánh hai xâu giống nhau hoàn toàn, sự khác nhau cho dù một ký tự trắng hoặc ký tự
							   # xuống dòng vẫn xem là khác nhau
	if out==ans: return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
def trinhcham_s2(out,ans): #Tương tự như trình chấm s1 nhưng KHÔNG phân biệt HOA/thường
	if out.lower()==ans.lower(): return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
@timeout(11)
def calll(p,timeout,inp):
	outp, err = p.communicate(timeout=timeout,input=inp)
	return outp,err

def chamcpp_pas(fn_exe,flog,tc,config):
	numtrue, checkSTOP=0,0
	#Kết thúc chấm ngay lập tức với những bài có test chấm bị TLE hoặc lỗi về bộ nhớ
	for i,d in enumerate(tc):
		createlog(flog,'----'+"test"+str(i)+': ')
		p=subprocess.Popen([fn_exe],stdout=subprocess.PIPE,stdin=subprocess.PIPE)
		try:
			start_time = time.time()
			outp, err = calll(p,config['exe'],d['inp'])#p.communicate(timeout=config['exe'],input=inp)
			finish_time= time.time()
			outp=outp.decode('utf-8')

			if(len(tc)==1 and tc[0]["out"]==""):#Trường hợp chấm ví dụ
				createlog(flog,outp+"\n-----xong-----",0)
			else:
				if config['tc']=='c1': check,statust=trinhcham_c1(d['out'],outp)
				if config['tc']=='c2': check,statust=trinhcham_c2(d['out'],outp)
				if config['tc']=='c3': check,statust=trinhcham_c3(d['out'],outp,config['e'])
				if config['tc']=='s1': check,statust=trinhcham_s1(d['out'],outp)
				if config['tc']=='s2': check,statust=trinhcham_s2(d['out'],outp)
				createlog(flog,statust)
				numtrue=numtrue+check
				createlog(flog,str(round(finish_time-start_time,3))+' (s)\n')
		except Exception as e:
			messerr=str(e)
			createlog(flog,"<span class='text-danger'>"+messerr+"</span>\n")
			#checkSTOP=1
		p.kill()
		if(tc[0]["out"]!=""):
			createlog(flog,'result: '+str(numtrue)+'/'+str(len(tc))+'\n',1)
		if checkSTOP==1: return numtrue
	return numtrue
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn
def sqlupdate(conn,fulltest,numtrue,log,id):
	sql = ''' UPDATE submitcode
              SET fulltest = ? , 
                  numtest = ? ,
                  log = ?,
                  graded=?
              WHERE id = ?'''
	cur = conn.cursor()
	cur.execute(sql, (fulltest,numtrue,log,1,id))
	conn.commit()

def convert_docx_to_pdf(conn):#Chuyển *docx sang pdf rồi đưa vào database
	for files in os.listdir("tmp"):
		if ".docx" not in files: continue
		if "hpcode" in files: continue
		if "_sol" in files: continue
		convert(os.path.join("tmp",files))
		fn=os.path.join("tmp",files.replace("docx","pdf"))
		idp=files.split(".")[0].lower()
		f=open(fn,"rb")
		data=f.read()
		f.close()
		sql = """UPDATE post 
	         SET pdf = ?
             WHERE id_p = ?;"""
		cur = conn.cursor()
		cur.execute(sql, (data,idp))
		conn.commit()
		os.remove(fn)
		os.remove(fn.replace("pdf","docx"))


def sqlupdate_p(conn,fulltest,idp): #update thêm 1 lượt AC cho bài tập
	sql = """UPDATE post 
	         SET ac = ac + ?
             WHERE id_p = ?;"""
	cur = conn.cursor()
	cur.execute(sql, (1 if fulltest else 0,idp))
	conn.commit()

def get_code_exam(conn):
	#Tìm bài chưa chấm tmp dạng [user].ext
	#Trả về (id của bản ghi trong Runexam,tên tệp,bộ test tương ứng của bài,mã bài tập)
	sql="""SELECT * 
			FROM Runexam
			WHERE graded = 0;"""
	cur = conn.cursor()
	cur.execute(sql)
	data=cur.fetchall()
	data.reverse()
	if(len(data)==0): return 0,0,0,0
	d=data[0]
	fn="tmp/"+d[2]+"."+d[4]
	f=open(fn,"w",encoding="utf-8")
	f.write(d[5].replace("\n",""))
	f.close()
	tc=[{"inp":d[3].encode(),"out":""}]

	sql = """UPDATE runexam 
	         SET graded = 1
             WHERE id = ?;"""
	cur = conn.cursor()
	cur.execute(sql, (d[0],))
	conn.commit()         
	return d[0],fn,tc,d[1]

def get_code_test(conn):
	#Tìm bài chưa chấm có test đầu tiên đưa vào thư mục tmp dạng idSubmit.ext
	#Trả về (id của bản ghi trong Submitcode,tên tệp,bộ test tương ứng của bài,mã bài tập)
	sql="""SELECT * 
			FROM submitcode
			WHERE graded = 0;"""
	cur = conn.cursor()
	cur.execute(sql)
	data=cur.fetchall()
	#data.reverse()
	for d in data:
		sql="""SELECT * 
				FROM testcase
				WHERE  post_id = ?;"""
		cur.execute(sql,(d[3],))
		tests=cur.fetchall()
		if len(tests)==0: continue
		if d[7] is None: continue
		if int(d[0])==24573:continue

		fn="tmp/"+str(d[0])+"."+d[6]
		f=open(fn,"w",encoding="utf-8")
		f.write(d[7].replace("\n",""))
		f.close()
		tc =[{"inp":t[1],"out":t[2].decode()} for t in tests]
		return d[0],fn,tc,d[3]
	return 0,0,0,0
def get_conf(idp):
	config={'exe':2,'py':2,'point':50,'tc':'c1','e':0.00001,'memory':1024}
	sql="""SELECT * 
		   FROM config
		   WHERE idp = ?;"""
	cur = conn.cursor()
	cur.execute(sql,(idp,))
	data=cur.fetchone()
	if len(data)>0:
		config['tc']=data[3]
		config['exe']=data[4]
		config['py']=data[5]
		config['memory']=data[6]
		config['e']=data[7]
	return config
def runtet():
	deletefilecode()
	time.sleep(1)
	ids,fn,tc,idp=get_code_exam(conn)#Lấy các bài nộp ví dụ
	if ids==0:#Nếu không có ví dụ
		ids,fn,tc,idp=get_code_test(conn) #mã bản ghi trong SubmitCode, tên file code, testcase, mã bài tập
	if ids==0: return
	config=get_conf(idp)
	flog=fn+".log" #File log
	fn_exe=fn[:-3]+'exe'
	ext=fn.split(".")[1]
	numtrue=0
	print(fn)
	if(ext in ['cpp','pas']):
		createlog(flog,'               Dịch file ['+fn+'\n',0)
		print('-------- Đang dịch...',end="")
		if ext=='cpp': x = subprocess.getoutput('g++ -std=c++1y ' + fn + ' -o ' + fn_exe+' -Wl,--stack,66060288')
		if ext=='pas': x = subprocess.getoutput('fpc ' + fn)
		print('Done...')
		print(x,end=" ")
		createlog(flog,x)
		if x=="" or 'compiled' in x:#Dịch thành công
			createlog(flog,'\nDịch thành công.\nĐang chấm...\n')
			print("-------- Đang chấm...",end="")
			numtrue=chamcpp_pas(fn_exe,flog,tc,config)
			
	if ext=='py':
		print("--------Đang chấm....")
		createlog(flog,'                ',0)
		for i,d in enumerate(tc):
			createlog(flog,'----'+"test"+str(i)+': ')
			#print('----'+"test"+str(i))
			try:
				x=subprocess.Popen(['python',fn],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
				start_time = time.time()
				outp, err=calll(x,config['py'],d["inp"])
				finish_time = time.time()
				outp=outp.decode('utf-8')
				if err.decode('utf-8')=="":
					if(len(tc)==1 and tc[0]["out"]==""):#Trường hợp chấm ví dụ
						createlog(flog,outp+"\n-----xong-----",0)
					else:
						if config['tc']=='c1': check,statust=trinhcham_c1(d['out'],outp)
						if config['tc']=='c2': check,statust=trinhcham_c2(d['out'],outp)
						if config['tc']=='c3': check,statust=trinhcham_c3(d['out'],outp,config['e'])
						if config['tc']=='s1': check,statust=trinhcham_s1(d['out'],outp)
						if config['tc']=='s2': check,statust=trinhcham_s2(d['out'],outp)
						createlog(flog,statust)
						numtrue=numtrue+check
						createlog(flog,str(round(finish_time-start_time,2))+' (s)\n')
				else:  createlog(flog,err.decode('utf-8'),0)
				
			except Exception as e:
				x.kill()
				err=str(e).split(']')[-1][2:] 
				createlog(flog,"<span class='text-danger'>"+err+"</span>\n")
				
		
	if(len(tc)==1 and tc[0]["out"]==""): 
		print("Chấm ví dụ: done")
		return
	createlog(flog,'result: '+str(numtrue)+'/'+str(len(tc))+'\n',1)
	createlog(flog,'======Chấm xong======\n')
	#Cập nhật dữ liệu vào Database
	log=""
	try:
		f=open(flog,"r",encoding="utf-8")
		log=f.read()
		f.close()
	except:
		log="result: "+str(numtrue)+"/"+str(len(tc))+" \nsorry! system can't create log for your solution"
	
	#if int(ids)>18000: 
	sqlupdate(conn,(numtrue==str(len(tc)) and numtrue>0),numtrue,log,ids)
	#sqlupdate_(conn,numtrue,log,ids)
	#sqlupdate_p(conn,(numtrue==total and numtrue>0),idp) #update thêm 1 lượt AC cho bài tập
	
	print('--------Done!')
pyid=[]
if __name__ == "__main__":
	conn=create_connection("../../../app.db")
	#runtet()
	#print(get_code_exam(conn))
	#convert_docx_to_pdf(conn)
	while 1:
		try:
			#convert_docx_to_pdf(conn)
			runtet()
		except Exception as e: 
			print(e)
