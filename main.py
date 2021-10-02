from werkzeug.wrappers import response
import tables
from flask import Flask, render_template, request
import random
import json
from keras.models import load_model
from pymysql.cursors import Cursor
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, render_template, request, redirect
from db_config import mysql
from tables import Results
from app import app
import pymysql
import numpy as np
import pickle
from nltk.stem import WordNetLemmatizer
import nltk
#nltk.download('popular')
lemmatizer = WordNetLemmatizer()


@app.route('/new_user')
def add_user_view():
    return render_template('add.html')


@app.route('/chat')
def chat_bot():
    return render_template('chatbot.html')


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    result = chatbot_response(userText)
    return result


@app.route('/add', methods=['POST'])
def add_user():
    conn = None
    cursor = None
    try:
        _name = request.form['inputName']
        _form_number = request.form['inputFormNumber']
        _case_number = request.form['inputCaseNumber']
        _case_status = request.form['inputCaseStatus']
        _form_description = request.form['inputFormDescription']
        _password = request.form['inputPassword']
        if _name and _form_number and _case_number and _case_status and _form_description and _password and request.method == 'POST':
            _hashed_password = generate_password_hash(_password)
            sql = "INSERT INTO tbl_user(user_name, form_number, case_number, case_status, form_description, user_password) VALUES(%s, %s, %s, %s, %s, %s)"
            data = (_name, _form_number, _case_number, _case_status,
                    _form_description, _hashed_password,)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            flash('User added successfully!')
            return redirect('/')
        else:
            return 'Error while adding user'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/')
def users():
    conn = None
    cursor = None
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user")
        rows = cursor.fetchall()
        table = Results(rows)
        table.border = True
        return render_template('users.html', table=table)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/edit/<int:id>')
def edit_view(id):
    conn = None
    cursor = None
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user WHERE user_id=%s", id)
        row = cursor.fetchone()
        if row:
            return render_template('edit.html', row=row)
        else:
            return 'Error loading #{id}'.format(id=id)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/update', methods=['POST'])
def update_user():
    conn = None
    cursor = None
    try:
        _name = request.form['inputName']
        _form_number = request.form['inputFormNumber']
        _case_number = request.form['inputCaseNumber']
        _case_status = request.form['inputCaseStatus']
        _form_description = request.form['inputFormDescription']
        _password = request.form['inputPassword']
        _id = request.form['id']
        if _name and _case_number and _password and _id and request.method == 'POST':
            _hashed_password = generate_password_hash(_password)
            print(_hashed_password)
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT case_status FROM tbl_user WHERE user_id=%s", '2')
            row = cursor.fetchone()
            table = Results(row)
            table.border = True
            if _case_status != row['case_status']:
                print('case changed')    
            print(str(row['case_status']))
            sql="UPDATE tbl_user SET user_name=%s, form_number=%s, case_number=%s, case_status=%s, form_description=%s, user_password=%s WHERE user_id=%s"
            data=(_name, _form_number, _case_number, _case_status,
                  _form_description, _hashed_password, _id,)
            conn=mysql.connect()
            cursor=conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            flash('User updated successfully!')
            return redirect('/')
        else:
            return 'Error while updating user'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@ app.route('/delete/<int:id>')
def delete_user(id):
    conn=None
    cursor=None
    try:
        conn=mysql.connect()
        cursor=conn.cursor()
        cursor.execute("DELETE FROM tbl_user WHERE user_id=%s", (id,))
        conn.commit()
        flash('User deleted successfully!')
        return redirect('/')
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# model = pickle.load(open('Chatbot.pkl','rb'))
model=load_model('model.h5')
intents=json.loads(open('data.json').read())
words=pickle.load(open('texts.pkl', 'rb'))
classes=pickle.load(open('labels.pkl', 'rb'))

def clean_up_sentence(sentence):
    # tokenize the pattern - split words into array
    sentence_words=nltk.word_tokenize(sentence)
    # stem each word - create short form for word
    sentence_words=[lemmatizer.lemmatize(
        word.lower()) for word in sentence_words]
    return sentence_words

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words=clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag=[0]*len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i]=1
                if show_details:
                    print("found in bag: %s" % w)
    return(np.array(bag))

context = {}

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p=bow(sentence, words, show_details=True)
    res=model.predict(np.array([p]))[0]
    ERROR_THRESHOLD=0.25
    results=[[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list=[]
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    return return_list

def getCaseNumber():
    conn=None
    cursor=None
    try:
        conn=mysql.connect()
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT case_number FROM tbl_user WHERE user_name=%s", name)
        row=cursor.fetchone()
        table=Results(row)
        table.border=True
        return str(row['case_number'])
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

    return response


def getResponse(ints, intents_json, show_details=True):
    list_of_intents = intents_json['intents']
    tag = ints[0]
    if type(ints) == list:
        print("message is a list")

    elif (type(ints)) == str:
        print('messsage its a string')
        tag = ints
    else:
        print("message is a tuple")

    caseNumber = ''
    while ints:
        for i in list_of_intents:
                if i['tag'] == tag[0] or type(tag) == str:

                    #creates context question and answer
                    if 'context_set' in i and len(context) == 0:
                        context[caseNumber] = i['context_set']
                        result = random.choice(i['responses'])
                        return result

                    #checks if there is any context to the question.
                    elif 'context_filter' in i == 'case_status' and caseNumber in context:
                        i = list_of_intents[5]
                        caseStatus = getCaseStatus(caseNumber)
                        result = random.choice(i['responses']) + caseStatus
                        context.clear()
                        return result
                    
                    #checks if there is more than one posibility
                    elif 1 < len(ints) and type(tag) != str:
                        for x in ints:
                            if 'context_filter' in i:
                                timeStamps = getTimeStamps(caseNumber)
                                result = random.choice(i['responses']) + timeStamps
                                tag = ints[0]
                                return result
                        else:
                            ints = ints[0]
                            break

                    elif type(tag) == str and context:
                        if i['tag'] == 'case_timestamp' and context[caseNumber] == ['case_timestamp']:
                            timeStamps = getTimeStamps(caseNumber = 'A231323')
                            result = random.choice(i['responses']) + timeStamps
                            tag = ints[0]
                            context.clear()
                            return result

                        elif i['tag'] == 'case_request' and context[caseNumber] == ['case_request']:
                            print(context)
                            i = list_of_intents[6]
                            caseStatus = getCaseStatus(tag)
                            result = random.choice(i['responses']) + ' ' + caseStatus
                            context.clear()
                            return result
                    
                    #makes sure there is no context to the question.
                    elif 'context' in i or len(context) == 0:
                        if 'context_filter' in i:
                            i = list_of_intents[3]
                            result = random.choice(i['responses'])
                            return result
                        else:
                            result = random.choice(i['responses'])
                            return result

                    #checks if the client is asking a context question.
                    elif len(context[caseNumber]) == 0 in context and type(tag) != str:
                        tag = context[caseNumber]
                        break
    return

## Get the timestamps of the case updates
def getTimeStamps(caseNumber):
    conn=None
    cursor=None
    try:
        conn=mysql.connect()
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user WHERE case_number=%s", caseNumber)
        row=cursor.fetchone()
        table=Results(row)
        table.border=True
        userId = str(row['user_id'])

        conn=mysql.connect()
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user_updates WHERE user_id=%s ORDER BY UpdatedOn DESC", userId)
        row=cursor.fetchone()
        table=Results(row)
        table.border=True
        result = str(row['UpdatedOn'])
        return result
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


    return

def chatbot_response(msg):
    if msg.startswith('A'):
        print('True')
        res=getResponse(msg, intents, 0)
        return res
    ints=predict_class(msg, model)

    res=getResponse(ints, intents, 0)
    return res

def getCaseStatus(caseNumber):
    conn=None
    cursor=None
    try:
        conn=mysql.connect()
        cursor=conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user WHERE case_number=%s", caseNumber)
        row=cursor.fetchone()
        table=Results(row)
        table.border=True
        return str(row['case_status'])
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run()
