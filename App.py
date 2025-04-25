#SET UP:

# 1. INSTALL BELOW LIBRARIES

        #pip install -r requirements.txt

import streamlit as st
import pandas as pd
import base64
import time,datetime
#libraries to parse the resume pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter

import io,random
from streamlit_tags import st_tags
from PIL import Image
from pymongo import MongoClient
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import pafy #for uploading youtube videos
import yt_dlp as youtube_dl
import plotly.express as px #to create visualisations at the admin session
import nltk
nltk.download('popular')


def fetch_yt_video(link):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'extract_flat': True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            return info.get('title', 'Video Title')
    except Exception as e:
        print(f"Error fetching video info: {e}")
        return "Interview Preparation Tips"

def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

# MongoDB connection
def get_mongo_client():
    connection_string = "mongodb+srv://admin:admin@cluster0.tdr9fja.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    return MongoClient(connection_string)

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    client = get_mongo_client()
    db = client['resume']  # Using 'resume' database
    collection = db['user_data']
    
    data = {
        'Name': name,
        'Email_ID': email,
        'resume_score': str(res_score),
        'Timestamp': timestamp,
        'Page_no': str(no_of_pages),
        'Predicted_Field': reco_field,
        'User_level': cand_level,
        'Actual_skills': skills,
        'Recommended_skills': recommended_skills,
        'Recommended_courses': courses
    }
    
    collection.insert_one(data)
    client.close()

def get_all_user_data():
    client = get_mongo_client()
    db = client['resume']
    collection = db['user_data']
    data = list(collection.find({}, {'_id': 0}))
    client.close()
    return data

st.set_page_config(
   page_title="AI Resume Analyzer",
   page_icon='./Logo/logo3.png',
)

def run():
    img = Image.open('./Logo/logo3.png')
    st.image(img)
    st.title("AI Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '[©Developed by CapedBaldy-v1](https://github.com/CapedBaldy-v1)'
    st.sidebar.markdown(link, unsafe_allow_html=True)

    if choice == 'User':
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload your resume, and get smart recommendations</h5>''',
                    unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(4)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >=3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)

                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',
                    value=resume_data['skills'],key = '1  ')

                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit', 'python', 'r', 'sql', 'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'plotly', 'sklearn', 'tensorflow', 'pytorch', 
                              'data analysis','keras', 'spark', 'hadoop', 'hive', 'pig', 'kafka', 'airflow', 'mlflow', 'dask', 'jupyter', 'colab', 'tableau', 'power bi', 'looker', 'excel', 'statistics', 'probability', 'linear algebra', 
                              'machine learning', 'data visualization','calculus', 'hypothesis testing', 'regression', 'classification', 'clustering', 'neural networks', 'cnn', 'rnn', 'lstm', 'transformers', 'nlp', 'computer vision', 
                              'opencv', 'pytesseract', 'spacy', 'nltk', 'gensim', 'huggingface', 'bert', 'gpt', 'xgboost', 'lightgbm', 'catboost', 'feature engineering', 'data cleaning', 'etl', 'data pipelines', 'data visualization', 
                              'data mining', 'time series', 'arima', 'prophet', 'anomaly detection', 'recommender systems', 'reinforcement learning', 'mlops', 'docker', 'kubernetes', 'aws sagemaker', 'azure ml', 'gcp ai', 'bigquery', 
                              'snowflake', 'databricks', 'elasticsearch', 'mongodb', 'redis', 'cassandra', 'neo4j', 'd3.js', 'plotly dash', 'streamlit', 'fastapi', 'flask', 'django', 'rest api', 'graphql', 'web scraping', 'beautifulsoup', 
                              'scrapy', 'selenium', 'pytorch lightning', 'kubeflow', 'prometheus', 'grafana', 'ml fairness', 'explainable ai', 'responsible ai', 'data governance', 'data privacy', 'gdpr']
                
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress', 'javascript', 'angular js', 'c#', 'flask', 'html5', 'css3', 'javascript', 'typescript', 'react', 'angular', 'vue', 'svelte', 
                               'next.js', 'nuxt.js', 'gatsby', 'remix', 'astro', 'node.js', 'express', 'nest.js', 'fastify', 'deno', 'bun', 'php', 'laravel', 'symfony', 'wordpress', 'drupal', 'python', 'django', 'flask', 'ruby', 'ruby on rails', 
                               'java', 'spring boot', 'c#', 'asp.net', 'go', 'gin', 'rust', 'actix', 'elixir', 'phoenix', 'graphql', 'apollo', 'rest', 'soap', 'grpc', 'websockets', 'webpack', 'vite', 'rollup', 'parcel', 'babel', 'esbuild', 
                               'swc', 'jest', 'mocha', 'chai', 'cypress', 'playwright', 'selenium', 'puppeteer', 'storybook', 'chromatic', 'eslint', 'prettier', 'stylelint', 'husky', 'lint-staged', 'docker', 'kubernetes', 'aws', 'azure', 
                               'gcp', 'vercel', 'netlify', 'cloudflare', 'heroku', 'digitalocean', 'linode', 'nginx', 'apache', 'caddy', 'traefik', 'mysql', 'postgresql', 'mongodb', 'redis', 'firebase', 'supabase', 'prisma', 'drizzle', 
                               'typeorm', 'sequelize', 'mongoose', 'knex', 'bookshelf', 'passport', 'jwt', 'oauth', 'openid', 'bcrypt', 'helmet', 'cors', 'csrf', 'xss', 'sql injection', 'csp', 'hsts', 'security headers', 'pwa', 'web components', 
                               'web assembly', 'three.js', 'd3.js', 'canvas', 'svg', 'webgl', 'web audio', 'web rtc', 'web sockets', 'service workers', 'indexeddb', 'localstorage', 'sessionstorage', 'cookies', 'web workers', 'shadow dom', 
                               'custom elements', 'html templates', 'css variables', 'css modules', 'sass', 'less', 'stylus', 'postcss', 'tailwind', 'bootstrap', 'material ui', 'chakra ui', 'ant design', 'semantic ui', 'foundation', 'bulma']
                
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy', 'java', 'kotlin', 'android studio', 'gradle', 'xml', 'jetpack compose', 'material design', 'mvvm', 'mvc', 'mvi', 'clean architecture', 
                                   'room database', 'sqlite', 'realm', 'firebase', 'firestore', 'retrofit', 'volley', 'okhttp', 'glide', 'picasso', 'coroutines', 'flow', 'livedata', 'viewmodel', 'navigation component', 'workmanager', 
                                   'hilt', 'dagger', 'koin', 'espresso', 'junit', 'mockito', 'robolectric', 'ui automator', 'appium', 'git', 'github', 'bitbucket', 'ci/cd', 'jenkins', 'fastlane', 'play console', 'in-app purchases', 'admob', 
                                   'maps sdk', 'location services', 'sensors', 'bluetooth', 'nfc', 'camera api', 'media player', 'exoplayer', 'notifications', 'foreground services', 'background services', 'broadcast receivers', 'content providers', 
                                   'permissions', 'deep links', 'app bundles', 'proguard', 'r8', 'multidex', 'ndk', 'jni', 'cmake', 'performance optimization', 'memory management', 'profiling', 'leakcanary', 'chrome devtools', 'accessibility', 
                                   'localization', 'dark theme', 'animations', 'transitions', 'custom views', 'canvas', 'opengl es', 'vulkan', 'wear os', 'android tv', 'android auto', 'instant apps', 'dynamic delivery', 'testflight', 
                                   'crashlytics', 'analytics', 'push notifications', 'work profiles', 'biometric auth', 'security', 'encryption', 'ssl pinning', 'obfuscation', 'motion layout', 'constraintlayout', 'coordinatorlayout', 
                                   'viewpager2', 'paging library', 'databinding', 'viewbinding', 'livedata', 'flows', 'channels']
                
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode', 'swift', 'objective-c', 'xcode', 'swiftui', 'uikit', 'storyboards', 'xib', 'cocoa touch', 'core data', 'realm', 'sqlite', 'firebase', 'cloudkit', 
                               'core animation', 'core graphics', 'core ml', 'arkit', 'create ml', 'combine', 'async/await', 'actors', 'swift concurrency', 'mvvm', 'viper', 'clean architecture', 'alamofire', 'urlsession', 'kingfisher', 
                               'sdwebimage', 'cocoapods', 'spm', 'carthage', 'fastlane', 'testflight', 'app store connect', 'in-app purchases', 'storekit', 'admob', 'mapkit', 'core location', 'core bluetooth', 'avfoundation', 'avkit', 
                               'push notifications', 'background modes', 'app extensions', 'widgets', 'share extensions', 'siri shortcuts', 'watchos', 'tvos', 'mac catalyst', 'uikit for mac', 'app clips', 'swift packages', 'xctest', 'xcuitest', 
                               'quick', 'nimble', 'snapshot testing', 'github actions', 'bitrise', 'circleci', 'git', 'github', 'bitbucket', 'code review', 'debugging', 'instruments', 'memory graphs', 'time profiler', 'energy log', 
                               'network link conditioner', 'accessibility', 'dynamic type', 'voiceover', 'localization', 'dark mode', 'adaptive layouts', 'size classes', 'autolayout', 'stack views', 'collection views', 'table views', 
                               'compositional layout', 'diffable data sources', 'core image', 'vision', 'natural language', 'pdfkit', 'webkit', 'wkwebview', 'safari extensions', 'app thinning', 'on-demand resources', 'code signing', 
                               'provisioning profiles', 'keychain', 'security', 'encryption', 'biometric auth', 'face id', 'touch id', 'swift playgrounds', 'xcode cloud', 'testflight', 'crashlytics', 'analytics', 'firebase', 'revenuecat', 
                               'fastlane', 'match', 'sigh', 'cert', 'deliver', 'pem', 'snapshot', 'frameit', 'badge', 'gym', 'scan', 'supply']
                
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects',
                                'adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience', 'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator', 'indesign', 'after effects', 
                                'principle', 'framer', 'protopie', 'axure', 'balsamiq', 'invision', 'marvel', 'zeplin', 'abstract', 'ux research', 'user interviews', 'surveys', 'personas', 'user journeys', 'empathy maps', 'information architecture', 
                                'wireframing', 'prototyping', 'mockups', 'design systems', 'style guides', 'typography', 'color theory', 'grid systems', 'whitespace', 'visual hierarchy', 'interaction design', 'microinteractions', 'animation', 
                                'motion design', 'responsive design', 'adaptive design', 'mobile first', 'atomic design', 'component libraries', 'accessibility', 'wcag', 'contrast checking', 'screen readers', 'voice ui', 'conversational ui', 
                                'gesture based ui', 'dark mode', 'light mode', 'material design', 'human interface guidelines', 'ios design', 'android design', 'web design', 'dashboard design', 'data visualization', 'icon design', 'illustration', 
                                'design thinking', 'double diamond', 'design sprints', 'usability testing', 'a/b testing', 'heatmaps', 'eye tracking', 'clickstream analysis', 'analytics', 'funnel analysis', 'user testing', 'guerrilla testing', 
                                'remote testing', 'card sorting', 'tree testing', 'first click testing', 'cognitive walkthrough', 'heuristic evaluation', 'nielsen heuristics', 'gestalt principles', 'fitts law', 'hicks law', 'millers law', 
                                'jakobs law', 'pareto principle', 'von restorff effect', 'serial position effect', 'ockhams razor', 'teslers law', 'doherty threshold', 'peak-end rule', 'persuasive design', 'gamification', 'emotional design', 
                                'service design', 'ux writing', 'content strategy', 'information design', 'wayfinding', 'navigation design', 'search design', 'form design', 'error handling', 'loading states', 'empty states', 'onboarding', 'tooltips', 
                                'modals', 'popovers']

                recommended_skills = []
                reco_field = ''
                rec_course = ''

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                
                keyword_sets = {
                    'Data Science': ds_keyword,
                    'Web Development': web_keyword,
                    'Android Development': android_keyword,
                    'IOS Development': ios_keyword,
                    'UI-UX Development': uiux_keyword
                }

                reco_field = None
                max_matches = 0
                matched_skills = {}

                for field, keywords in keyword_sets.items():
                    current_matches = 0
                    current_matched_skills = []
                    for skill in resume_data['skills']:
                        if skill.lower() in keywords:
                            current_matches += 1
                            current_matched_skills.append(skill.lower())

                    if current_matches > max_matches:
                        max_matches = current_matches
                        reco_field = field
                        matched_skills = current_matched_skills
                    elif current_matches == max_matches and current_matches > 0:
                        pass

                if reco_field:
                    st.success(f"** Our analysis says you are looking for {reco_field} Jobs.**")
                    print("Matched skills:", ", ".join(matched_skills))

                    if reco_field == 'Data Science':
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        rec_course = course_recommender(ds_course)
                    elif reco_field == 'Web Development':
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        rec_course = course_recommender(web_course)
                    elif reco_field == 'Android Development':
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        rec_course = course_recommender(android_course)
                    elif reco_field == 'IOS Development':
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        rec_course = course_recommender(ios_course)
                    elif reco_field == 'UI-UX Development':
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        rec_course = course_recommender(uiux_course)

                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                elif resume_data and 'skills' in resume_data and not resume_data['skills']:
                    st.warning("No skills found in the uploaded resume.")
                else:
                    st.info("Please upload a resume to get job role recommendations.")

                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)

                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'objective' in resume_text.lower():
                    resume_score = resume_score+20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'declaration' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration/h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Declaration. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',unsafe_allow_html=True)

                if 'hobbies' in resume_text.lower() or 'dnterests' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'achievement' in resume_text.lower() or 'experience' in resume_text.lower() or 'internship' in resume_text.lower() or 'work experience' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'projects' in resume_text.lower():
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")
                st.balloons()

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                              str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                              str(recommended_skills), str(rec_course))

                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                res_vid_title = fetch_yt_video(resume_vid)
                st.subheader("✅ **"+res_vid_title+"**")
                st.video(resume_vid)

                st.header("**Bonus Video for Interview Tips💡**")
                interview_vid = random.choice(interview_videos)
                int_vid_title = fetch_yt_video(interview_vid)
                st.subheader("✅ **" + int_vid_title + "**")
                st.video(interview_vid)

            else:
                st.error('Something went wrong..')
    else:
        st.success('Welcome to Admin Side')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'admin' and ad_password == 'admin':
                st.success("Welcome Administrator !")
                
                data = get_all_user_data()
                if data:
                    st.header("**User's Data**")
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    st.markdown(get_table_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)
                    
                    st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                    labels = df['Predicted_Field'].unique()
                    values = df['Predicted_Field'].value_counts()
                    fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills')
                    st.plotly_chart(fig)

                    st.subheader("**Pie-Chart for User's Experienced Level**")
                    labels = df['User_level'].unique()
                    values = df['User_level'].value_counts()
                    fig = px.pie(df, values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                    st.plotly_chart(fig)
                else:
                    st.warning("No user data found in the database")
            else:
                st.error("Wrong ID & Password Provided")

run()
