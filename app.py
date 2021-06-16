from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
import bcrypt
import pandas as pd
from werkzeug.utils import secure_filename
import random
from flask_mail import Mail, Message
import csv
from io import StringIO

  
app = Flask(__name__)

environment_configuration = os.environ['CONFIGURATION_SETUP']
app.config.from_object(environment_configuration)

mail = Mail(app)
  

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOADED_DATA_DEST = os.path.join(basedir, 'static', 'uploads')
 
mysql = MySQL(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    print(error)
    return render_template('500.html',Error=error),500

@app.route('/',methods = ['GET'])
def index():
    return redirect('/login')

@app.route('/login', methods =['GET', 'POST'])
def login():
    
    if 'username' not in session:
        msg = ''
        if request.method == 'POST':
            if 'username' in request.form and 'password' in request.form and 'dropdown' in request.form:
                username = request.form['username']
                password = request.form['password'].encode('utf-8')
                member= request.form['dropdown']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                if member== 'student':

                    cursor.execute('SELECT * FROM student WHERE roll_no = %s', (username, ))
                    student = cursor.fetchone()
                    if student is not None:
                        pswd=student['password'].encode('utf-8')

                        if bcrypt.checkpw(password, pswd):
                            session['loggedin'] = True
                            session['username'] = student['roll_no']
                            msg = 'Logged in successfully !'
                            resp = make_response(redirect(f'/students/{username}'))
                            resp.set_cookie('userID', username)
                            return resp
                            
                        else:
                            msg = 'Incorrect username / password !'
                            return render_template('login.html', msg = msg)

                    elif student is None:
                        msg = 'Student is not registered'
                        return render_template('login.html', msg = msg)
                   


                else:
                    cursor.execute('SELECT * FROM adminn WHERE email_id = %s', (username, ))
                    admin = cursor.fetchone()

                    if admin is not None:

                        pswd=admin['password'].encode('utf-8')

                        if bcrypt.checkpw(password, pswd):
                            
                            session['loggedin'] = True
                            session['admin'] = True
                            session['username'] = admin['email_id']
                            msg = 'Logged in successfully !'
                            resp = make_response(redirect(f'/admins/{username}'))
                            resp.set_cookie('userID', username)
                            return resp
                            
                        else:
                            msg = 'Incorrect username / password !'
                            return render_template('login.html', msg = msg)

                    elif admin is None:
                        msg = 'Admin is not registered'
                        return render_template('login.html', msg = msg)

        elif request.method == 'GET':
            return render_template('login.html',msg= msg)

    else:
        return render_template('login.html',loggedin='true')

@app.route('/logout')
def logout():
    if 'username' in session:
        if 'admin' in session:
            session.pop('admin', None)
        session.pop('username', None)
        session.pop('loggedin',None)
    return redirect(url_for('login'))

@app.route('/uploadstudentcsv', methods =['POST'])
def StudentCsv():

    if request.method == 'POST' and 'username' in session and 'admin' in session:   
        msg = ''
        id = session['username']
        if request.files:

            data= request.files["csv"]
            
            if os.path.splitext(data.filename)[-1] != '.csv':
                return 'ONLY CSV FILES ARE ALLOWED'
            data.save(os.path.join(UPLOADED_DATA_DEST, secure_filename(data.filename)))
            print("file saved")

            # read file
            path= os.path.join(UPLOADED_DATA_DEST, secure_filename(data.filename)).replace('\\','/')
            df= pd.read_csv(path)
            print(df.head())
            print("file read")

            # delete file after reading 
            os.remove(os.path.join(UPLOADED_DATA_DEST,secure_filename(data.filename)))

            # Insert DataFrame to Table
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            password='pass'.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password, salt)

            for row in df.itertuples():
                cursor.execute('SELECT * FROM student WHERE roll_no = %s', (row.roll_no, ))
                student = cursor.fetchone()
                if student is not None:
                    program_attended = row.program_attended.split(',')
                    for i in range(len(program_attended)):
                        cursor.execute('SELECT trained_hours from attends WHERE roll_no=%s and program_id=%s',(row.roll_no, program_attended[i].strip()))
                        record=cursor.fetchone()
                        print(record)
                        if record is not None:
                            duration= int(record['trained_hours'])+1
                            cursor.execute('UPDATE attends SET trained_hours=%s where roll_no=%s and program_id=%s',(duration,row.roll_no,program_attended[i].strip()))
                        else:
                            cursor.execute('INSERT INTO attends VALUES (%s,%s,%s)',(row.roll_no,program_attended[i],1))
                else:
                    cursor.execute('INSERT INTO student (roll_no, name, email_id, year, branch, job_offer, phone_no, password) VALUES (%s, %s, % s, %s, %s, %s, %s, %s)', (row.roll_no, row.name, row.email_id, row.year, row.branch, row.job_offer, row.phone_no, hashed))
                    for i in set(row.program_attended.split(',')):
                        cursor.execute('INSERT INTO attends VALUES (%s,%s, %s)',(row.roll_no, i.strip(), 1) )
            mysql.connection.commit()
            msg = 'You have successfully added student record!'
            return redirect(f'/admins/{id}')
        else: 
            return 'File to be uploaded is missing'
    else:
        return render_template('401.html')

@app.route('/uploadprogramcsv', methods =['POST']) 
def ProgramCsv():
    msg = ''
    if request.method == 'POST' and 'username' in session and 'admin' in session:
        id = session['username']
        # save uploaded file 
        print(request.files)
        if request.files:
            data= request.files["csv"]
            if os.path.splitext(data.filename)[-1] != '.csv':
                return 'ONLY CSV FILES ARE ALLOWED'

            data.save(os.path.join(UPLOADED_DATA_DEST, secure_filename(data.filename)))
            print("file saved")

            # read file
            path= os.path.join(UPLOADED_DATA_DEST, secure_filename(data.filename)).replace('\\','/')
            df= pd.read_csv(path)
            print(df.head())
            print("file read")

            # delete file after reading 
            os.remove(os.path.join(UPLOADED_DATA_DEST,secure_filename(data.filename)))

            # Insert DataFrame to Table
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            for row in df.itertuples():
                cursor.execute('INSERT INTO program VALUES (%s, %s, % s, %s)', (row.program_id, row.program_name, row.description, row.duration))
            mysql.connection.commit()
            msg = 'You have successfully added program record!'
            return redirect(f'/admins/{id}')
        else: 
            return 'File to be uploaded is missing'
    else:
        return render_template('401.html')

@app.route('/addStudent', methods =['POST'])
def addStudent():
    if 'username' in session and 'admin' in session:
        if request.method == 'POST':
            if  'roll_no' in request.form and 'year' in request.form and 'branch' in request.form and 'name' in request.form and 'phone_no' in request.form and 'job_offer' in request.form and 'email_id' in request.form and 'password' in request.form and 'programs' in request.form:
                msg = ''
                id = session['username']
                roll_no=request.form['roll_no']
                name = request.form['name']
                email_id = request.form['email_id']
                year=request.form['year']
                branch=request.form['branch']
                job_offer=request.form['job_offer']
                phone_no=request.form['phone_no']
                password = request.form['password'].encode("utf-8")
                program_ids = request.form['programs'].split(',')
                print('check1')
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password, salt)

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM student WHERE roll_no = %s', (roll_no, ))
                student = cursor.fetchone()
                if student is not None:
                    # attend table
                    for i in range(len(program_ids)):
                        cursor.execute('SELECT trained_hours from attends WHERE roll_no=%s and program_id=%s',(roll_no, program_ids[i].strip()))
                        record=cursor.fetchone()
                        print(record)
                        if record is not None:
                            duration= int(record['trained_hours'])+1

                            cursor.execute('UPDATE attends SET trained_hours=%s where roll_no=%s and program_id=%s',(duration,roll_no,program_ids[i].strip()))
                        else:
                            cursor.execute('INSERT INTO attends VALUES (%s,%s,%s)',(roll_no,program_ids[i],1))
                    mysql.connection.commit()
                    return redirect(f'/admins/{id}')

                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email_id):
                    msg = 'Invalid email address !'
                elif not re.match(r'[A-Za-z0-9]+', name):
                    msg = 'Username must contain only characters and numbers !'
                elif not name or not roll_no or not email_id or not year or not branch or not phone_no or not job_offer:
                    msg = 'Please fill out the form !'
                else:
                    cursor.execute('INSERT INTO student (roll_no, name, email_id, year, branch, job_offer, phone_no, password) VALUES (%s, %s, % s, %s, %s, %s, %s, %s)', (roll_no, name, email_id, year, branch, job_offer, phone_no, hashed))
                    for i in range(len(program_ids)):
                        cursor.execute('INSERT INTO attends VALUES (%s,%s,%s)',(roll_no,program_ids[i],1))
                    mysql.connection.commit()
                    msg = 'You have successfully added student record!'
                    return redirect(f'/admins/{id}')
                return msg
            else:
                return "Fields are missing"
        else:
            return render_template('404.html')
    else:
        return render_template('401.html')

@app.route('/addProgram', methods =['POST'])
def addProgram():
    msg = ''
    if request.method == 'POST' and 'username' in session and 'admin' in session:
        if 'program_id' in request.form and 'program_name' in request.form and 'description' in request.form and 'duration' in request.form:
            id = session['username']
            program_id=request.form['program_id']
            program_name=request.form['program_name']
            description=request.form['description'].strip()
            duration=request.form['duration']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM program WHERE program_id = %s', (program_id, ))
            program = cursor.fetchone()
            if program:
                msg = 'Program already exists !'
                return msg
            elif not program_id or not program_name or not description or not duration:
                msg = 'Please fill out the form !'
                return msg
            else:
                cursor.execute('INSERT INTO program VALUES (%s, %s, % s, %s)', (program_id, program_name, description, duration))
                mysql.connection.commit()
                msg = 'You have successfully added program record!'
                return redirect(f'/admins/{id}')
        else:
            return 'Fields are missing'
    else:
        return render_template('401.html')

@app.route('/updateProgramInfo/<id>', methods =['GET','POST'])   
def updateProgramInfo(id):
    if 'username' in session and 'admin' in session:
        username = session['username']
        if request.method == 'POST':
            msg = ''
            if 'program_id' in request.form and 'program_name' in request.form and 'description' in request.form and 'duration' in request.form:
                program_id=request.form['program_id']
                program_name=request.form['program_name']
                description=request.form['description'].strip()
                duration=request.form['duration']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM program WHERE program_id = % s', (id, ))
                program = cursor.fetchone()
                if program is not None:
                    cursor.execute('UPDATE program set program_id=%s, program_name=%s, description=%s, duration=%s WHERE program_id=%s ', (program_id, program_name, description, duration, id))
                    mysql.connection.commit()
                    msg = 'You have successfully updated the program!'
                    return redirect(f'/admins/{username}')
                else:
                    msg = 'The Program you wish to update does not exist'
                    return msg
        elif request.method  == 'GET':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM program WHERE program_id = % s', (id, ))
            program = cursor.fetchone()
            return render_template('EditProgramTable.html', program= program)
    else:
        return render_template('401.html')
                
@app.route('/updateStudentInfo', methods =['POST'])
def updateStudentInfo():
    if 'username' in session and 'admin' not in session:
        if request.method == 'POST':
            if 'year' in request.form and 'branch' in request.form and 'name' in request.form and 'phone_no' in request.form and 'job_offer' in request.form and 'email_id' in request.form :
                msg = ''
                roll_no=session['username']
                name = request.form['name']
                email_id = request.form['email_id']
                year=request.form['year']
                branch=request.form['branch']
                job_offer=request.form['job_offer']
                phone_no=request.form['phone_no']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM student WHERE roll_no = % s', (roll_no, ))
                student = cursor.fetchone()
                if student is not None:
                    cursor.execute('UPDATE student set name=%s, email_id=%s, year=%s, branch=%s, job_offer=%s, phone_no=%s WHERE roll_no=%s', (name, email_id, year, branch, job_offer, phone_no, roll_no))
                    mysql.connection.commit()
                    msg = 'You have successfully updated student record!'
                    print(msg)
                    return redirect(f'/students/{roll_no}')
                else:
                    msg = 'The Student you wish to update does not exist'
                    return msg
            else:
                return 'Fields are missing'
    else:
        return render_template('401.html') 

@app.route('/updateStudentInfoByAdmin/<id>', methods =['GET','POST'])  
def updateStudentInfoByAdmin(id):
    if 'username' in session and 'admin' in session:
        msg = ''
        if request.method == 'POST':
            if 'year' in request.form and  'branch' in request.form and 'name' in request.form and 'phone_no' in request.form and 'job_offer' in request.form and 'email_id' in request.form :
                email_id_admin=session['username'] 
                name = request.form['name']
                email_id = request.form['email_id']
                roll_no = request.form['roll_no']
                year=request.form['year']
                branch=request.form['branch']
                job_offer=request.form['job_offer']
                phone_no=request.form['phone_no']
                programs= request.form['programs'].split(',')
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM student WHERE roll_no = % s', (id, ))
                student = cursor.fetchone()
                if student is not None:
                    cursor.execute('UPDATE student set roll_no=%s, name=%s, email_id=%s, year=%s, branch=%s, job_offer=%s, phone_no=%s WHERE roll_no=%s', (roll_no,name, email_id, year, branch, job_offer, phone_no,id))
                    cursor.execute('SELECT program_id FROM attends where roll_no=%s',(id,))
                    program_ids= cursor.fetchall()
                    result =[]
                    for i in range(len(program_ids)):
                        result.append(program_ids[i]['program_id'].strip())


                    programs= [p.strip() for p in programs]
                    for prog in programs:
                        if prog not in result:
                            cursor.execute('INSERT INTO attends VALUES (%s,%s,%s)',(id,prog,1)) 

                    for prog in result:
                        if prog not in programs:
                            cursor.execute('DELETE FROM attends WHERE  roll_no = %s and program_id=%s',(id,prog))


                    mysql.connection.commit()
                    msg = 'You have successfully updated student record!'
                    print(msg)
                    return redirect(f'/admins/{email_id_admin}')
                else:
                    msg = 'The Student you wish to update does not exist'
                    return msg
            else:
                return 'Fields are missing'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM student WHERE roll_no = % s', (id, ))
            student = cursor.fetchone()
            cursor.execute('SELECT program_id, trained_hours FROM attends where roll_no=%s',(id,))
            programs = cursor.fetchall()
            cursor.execute('SELECT program_id FROM attends where roll_no=%s',(id,))
            programsss = cursor.fetchall()
            if student['job_offer'] == 'YES':
                options = ['YES','NO']
            else: options = ['NO','YES']
            res=[]
            for i in range(len(programs)):
                res.append(programs[i]['program_id'])
            return render_template('EditStudentTable.html', student= student,option_list=options, programs= ','.join(res))

    return render_template('401.html')

@app.route('/updateAdminInfo', methods =['POST'])
def updateAdminInfo():
    msg = ''
    if request.method== 'POST' and 'username' in session:
        if 'name' in request.form and 'phone_no' in request.form:
            email_id = session['username']
            name = request.form['name']
            phone_no=request.form['phone_no']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM adminn WHERE email_id = % s', (email_id, ))
            admin = cursor.fetchone()
            if admin is not None:   
                cursor.execute('UPDATE adminn set name=%s,phone_no=%s  WHERE email_id=%s', ( name , phone_no,email_id))
                mysql.connection.commit()
                msg = 'You have successfully updated admin record!'
                return redirect(f'/admins/{email_id}')
            else:
                msg = 'The admin you wish to update is not registered.'
                return msg
        else:
            return 'Fields are missing'
    else:
        return render_template('401.html')
            
@app.route('/download_student_csv',methods=['GET'])
def downloadStudentCsv():
    if request.method =='GET' and not session.get('username') is None and 'admin' in session :
        cursor=mysql.connection.cursor(MySQLdb.cursors.Cursor)
        si = StringIO()
        cw = csv.writer(si)
        cursor.execute('SELECT roll_no, name, email_id, year, phone_no, branch, job_offer from student')
        student_records = list(cursor.fetchall())
        for i in range(len(student_records)):
            student_records[i] = list(student_records[i])
            roll = student_records[i][0]
            cursor.execute('SELECT program_id,trained_hours from attends where roll_no=%s',(roll,))
            result = cursor.fetchall()
            student_records[i].append(result)

        mysql.connection.commit()
        cw.writerow(['roll_no', 'name', 'email_id', 'year', 'phone_no', 'branch', 'job_offer', 'Program TH'])
        cw.writerows(student_records)
        response = make_response(si.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=student.csv'
        response.headers["Content-type"] = "text/csv"
        return response
    return render_template('401.html')     

@app.route('/download_program_csv',methods=['GET'])
def downloadProgramCsv():
    if request.method =='GET' and not session.get('username') is None and 'admin' in session:
        cursor=mysql.connection.cursor(MySQLdb.cursors.Cursor)
        si = StringIO()
        cw = csv.writer(si)
        cursor.execute('SELECT * from program')
        program_records = cursor.fetchall()
        mysql.connection.commit()
        cw.writerow([i[0] for i in cursor.description])
        cw.writerows(program_records)
        response = make_response(si.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=program.csv'
        response.headers["Content-type"] = "text/csv"
        return response
    return render_template('401.html') 

@app.route('/deleteProgramInfo/<id>', methods =['GET'])
def deleteProgramInfo(id):
    if request.method == 'GET' and 'username' in session and 'admin' in session:
        username = session['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE from program WHERE program_id=%s', (id, ))
        mysql.connection.commit()
        msg = 'You have successfully deleted program record!'
        return redirect(f'/admins/{username}')
    return render_template('401.html')

@app.route('/deleteStudentInfo/<roll>', methods =['GET']) 
def deleteStudentInfo(roll):
    if request.method == 'GET' and 'username' in session and 'admin' in session:
        username = session['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE from student WHERE roll_no=%s', (roll, ))
        mysql.connection.commit()
        return redirect(f'/admins/{username}')
    return render_template('401.html')

@app.route('/admins/<id>', methods =['GET'])
def adminInfo(id):

    if request.method == 'GET' and not session.get('username') is None and request.cookies.get('userID')==str(id) and 'admin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT  name, email_id,phone_no  from adminn where email_id=%s',(id,))
        admin_record = cursor.fetchone()

        cursor.execute('SELECT p.program_id,p.program_name,p.description,p.duration from program p')
        program_records = cursor.fetchall()

        cursor.execute('SELECT roll_no, name, email_id, year, phone_no, branch, job_offer from student')
        student_records = list(cursor.fetchall())
        for i in range(len(student_records)):
            roll = student_records[i]['roll_no']
            cursor.execute('SELECT program_id,trained_hours from attends where roll_no=%s',(roll,))
            result = cursor.fetchall()
            student_records[i]['program_attended'] = result

        mysql.connection.commit()
        msg = 'Successful!'
        return render_template('index2.html',admin_record =admin_record,program_records = program_records, student_records=student_records)
    return render_template('NotLoggedIn.html')


@app.route('/students/<id>', methods =['GET'])
def showStudent(id):

    if request.method == 'GET' and not session.get('username') is None and request.cookies.get('userID')==str(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT roll_no, name, email_id, year, branch, job_offer, phone_no from student where roll_no=%s',(id,))
        student_record = cursor.fetchone()
        if student_record['job_offer'] == 'YES':
            options = ['YES','NO']
        else: options = ['NO','YES']
        cursor.execute('SELECT p.program_id,p.program_name,p.description,p.duration,a.trained_hours from student s,program p, attends a WHERE s.roll_no=a.roll_no and p.program_id=a.program_id and s.roll_no = %s',(id,))
        program_records = cursor.fetchall()
        mysql.connection.commit()
        msg = 'You have successfully fetched a program record!'
        return render_template('index.html',student_record =student_record, program_record = program_records,option_list=options)
    return render_template('NotLoggedIn.html')

#Fetch result on basis of multiple fields
@app.route('/query', methods =['POST'])  
def query():
    if request.method == 'POST' and 'admin' in session and 'username' in session:
        if 'attribute' in request.form and 'val' in request.form and 'programid' in request.form:
            field= request.form['attribute']
            value = request.form['val']
            program_id= request.form['programid']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            if value=='' and program_id=='':
                # fetchall
                cursor.execute('SELECT roll_no,name, email_id, year, phone_no, branch, job_offer FROM student')
                result= cursor.fetchall()
            
            elif field== 'year':
                if program_id=='':
                    cursor.execute('SELECT roll_no,name, email_id, year, phone_no, branch, job_offer FROM student WHERE year=%s',(value,))

                else:
                    cursor.execute('SELECT s.roll_no,name, email_id, year, phone_no, branch, job_offer FROM student s, attends a, program p WHERE s.roll_no=a.roll_no and a.program_id=p.program_id and s.year=%s and p.program_id=%s',(value,program_id))

                result = cursor.fetchall()
                mysql.connection.commit()

            elif field== 'branch' :
                if program_id=='':
                    cursor.execute('SELECT roll_no,name, email_id, year, phone_no, branch, job_offer FROM student WHERE branch=%s',(value,))
                else:
                    cursor.execute('SELECT s.roll_no,name, email_id, year, phone_no, branch, job_offer FROM student s, attends a, program p WHERE s.roll_no=a.roll_no and a.program_id=p.program_id and s.branch=%s and p.program_id=%s',(value,program_id))
                
                result = cursor.fetchall()
                mysql.connection.commit()
               
            elif field=='job_offer':
                if program_id=='':
                    cursor.execute('SELECT roll_no,name, email_id, year, phone_no, branch, job_offer FROM student WHERE job_offer=%s',(value,))
                else:
                    cursor.execute('SELECT s.roll_no,name, email_id, year, phone_no, branch, job_offer FROM student s, attends a, program p WHERE s.roll_no=a.roll_no and a.program_id=p.program_id and s.job_offer=%s and p.program_id=%s',(value,program_id))
                result = cursor.fetchall()
                mysql.connection.commit()

            df = pd.DataFrame(result)
            filename = 'query_' + session['username'] + '.xlsx'
            df.to_excel('./static/Queries/'+ filename,index=False)

            return render_template('QueryTable.html',student_records = result,field=field,val=value,progid=program_id,filename=filename)
        else: return 'Fields are missing'
    return render_template('401.html')

#function to send OTP to reset mail
def send_email(email_id,pswd):
    print('sending')
    msg= Message('Hello', sender = 'hh5094266@gmail.com', recipients = [email_id])
    msg.body= 'This is One time password to login. You can change password once you login in. One Time Password is : '+ str(pswd)[2:-1]
    print(str(pswd)[2:-1])
    mail.send(msg)
    print ('Sent')

#function for forgot password. OTP sent on mail to reset the password
@app.route('/forgotPassword', methods =['GET','POST'])
def ForgotPassword():
    msg=''
    if request.method=='GET':
        return render_template('password.html')

    elif request.method=='POST':
        if 'member' in request.form and 'email_id' in request.form:
            member=request.form['member']
            email_id = request.form['email_id']
            pswd = ''.join(random.sample(list('0123456789abcdefghijklmnopqrstuvwxyz'),8)).encode('utf-8')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            if member=='student':
                print('student')
                cursor.execute('SELECT * from student WHERE email_id=%s',(email_id,))
                student= cursor.fetchone()
                if student is not None:
                    salt = bcrypt.gensalt()
                    hashed = bcrypt.hashpw(pswd, salt)                                         
                    cursor.execute('UPDATE student set password= %s WHERE email_id=%s',(hashed, email_id))
                    send_email(email_id,pswd)
                    mysql.connection.commit()
                    return render_template('login.html')
                else:
                    mysql.connection.commit()
                    msg='Email is not registered.'
                    return render_template('password.html', msg=msg)
            else:
                cursor.execute('SELECT * from adminn WHERE email_id=%s',(email_id,))
                admin= cursor.fetchone()
                if admin is not None:
                    salt = bcrypt.gensalt()
                    hashed = bcrypt.hashpw(pswd, salt)
                    cursor.execute('UPDATE adminn set password= %s WHERE email_id=%s',(hashed, email_id))
                    send_email(email_id,pswd)
                    mysql.connection.commit()
                    render_template('login.html')
                else:
                    mysql.connection.commit()
                    msg='Email is not registered.'
                    return render_template('password.html', msg=msg)
        else:
            return 'Fields are missing'
    return 'successful'

#function to change password for admin
@app.route('/admin/changePassword', methods =['POST'])
def AdminChangePassword():
    if request.method== 'POST'  and 'username' in session and 'admin' in session:
        if 'old_pass' in request.form and 'new_pass' in request.form and 'confirm_pass' in request.form:
            id= session['username']
            old_pass= request.form['old_pass'].encode("utf-8")
            new_pass= request.form['new_pass'].encode("utf-8")
            confirm_pass= request.form['confirm_pass'].encode("utf-8")

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute('SELECT * FROM adminn WHERE email_id = %s', (id, ))
            admin = cursor.fetchone()
            if admin is not None:
                pswd = admin['password'].encode('utf-8')
                if bcrypt.checkpw(old_pass, pswd):
                    if new_pass==confirm_pass:
                        salt = bcrypt.gensalt()
                        hashed = bcrypt.hashpw(new_pass, salt)
                        cursor.execute('UPDATE adminn set password=%s where email_id=%s ',(hashed, id))
                        mysql.connection.commit()
                        msg='You have successfully changed your password.'
                        return render_template('passchanged.html')
                    else:
                        msg= 'New password and confirm password do not match'
                        return msg

                else:
                    msg= 'Wrong password!'
                    return msg
            else:
                msg = 'Admin is not registered.' 
                return msg
        else:
            return 'Fields are missing'

    return render_template('401.html')


#function to change password for the student
@app.route('/student/changePassword', methods =['POST'])
def StudentChangePassword():
    if request.method== 'POST' and 'username' in session: 
        if 'old_pass' in request.form and 'new_pass' in request.form and 'confirm_pass' in request.form:
            id= session['username']
            old_pass= request.form['old_pass'].encode("utf-8")
            new_pass= request.form['new_pass'].encode("utf-8")
            confirm_pass= request.form['confirm_pass'].encode("utf-8")

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute('SELECT * FROM student WHERE roll_no = %s', (id, ))
            student = cursor.fetchone()
            if student is not None:
                pswd = student['password'].encode('utf-8')
                if bcrypt.checkpw(old_pass, pswd):
                    if new_pass==confirm_pass:
                        salt = bcrypt.gensalt()
                        hashed = bcrypt.hashpw(new_pass, salt)
                        cursor.execute('UPDATE student set password=%s where roll_no=%s ',(hashed, id))
                        mysql.connection.commit()
                        msg='You have successfully changed your password.'
                        return render_template('passchanged.html')
                    else:
                        msg= 'New password and confirm password do not match'
                        return msg

                else:
                    msg= 'Wrong password!'
                    return msg
            else:
                msg = 'Student is not registered.' 
                return msg
        else:
            return 'Fields are missing'

    return render_template('401.html')

@app.route('/returnToMain', methods =['GET'])
def returnToMain():
    if 'username' in session and 'admin' in session:
        username=session['username']
        return redirect(f'/admins/{username}')
    elif 'username' in session:
        username = session['username']
        return redirect(f'/students/{username}')
    return render_template('401.html')


if __name__ == '__main__':
   app.run()