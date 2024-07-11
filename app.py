from flask import Flask, request, render_template, url_for
import instaloader
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

def scrape_profile_data(username):
    loader = instaloader.Instaloader()
    profile = instaloader.Profile.from_username(loader.context, username)
    
    profile_data = {
        'profile_picture': profile.profile_pic_url,
        'posts': profile.mediacount,
        'followers': profile.followers,
        'following': profile.followees
    }
    
    return profile_data

def calculate_fraud_score(profile_data):
    score = 0
    if not profile_data.get('profile_picture'):
        score += 30
    if profile_data.get('posts', 0) < 5:
        score += 20
    if profile_data.get('followers', 0) < 100:
        score += 20
    if profile_data.get('following', 0) > 1000:
        score += 30
    if profile_data.get('followers') < profile_data.get('following'):
        score += 30
    
    return score

def categorize_account(fraud_score):
    if fraud_score >= 80:
        return "Fake"
    elif 50 <= fraud_score < 80:
        return "Warning"
    else:
        return "Real"

def save_to_sqlite(df, db_name='account_analysis.db', table_name='account_analysis'):
    try:
        conn = sqlite3.connect(db_name)
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.close()
        print(f"Results saved to {db_name} in table {table_name}")
    except Exception as e:
        print(f"Error saving to SQLite database: {e}")

def analyze_usernames(usernames):
    results = []
    
    for username in usernames:
        try:
            profile_data = scrape_profile_data(username)
        except Exception as e:
            print(f"Error scraping profile for {username}: {e}")
            continue
        
        fraud_score = calculate_fraud_score(profile_data)
        category = categorize_account(fraud_score)
        
        results.append({
            'username': username,
            'fraud_score': fraud_score,
            'category': category,
            'posts': profile_data['posts'],
            'followers': profile_data['followers'],
            'following': profile_data['following']
        })
        
    df = pd.DataFrame(results)
    csv_filename = 'account_analysis_results.csv'
    df.to_csv(csv_filename, index=False)
    save_to_sqlite(df)
    
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        usernames = request.form['usernames'].split()
        results = analyze_usernames(usernames)
        return render_template('results.html', results=results)
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
