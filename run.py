from app import create_app

# 1. Application Factory ကနေ app ကို တည်ဆောက်ခိုင်းခြင်း
app = create_app()

# 2. ဒီ file ကို တိုက်ရိုက် run တဲ့အခါမှာပဲ server ကို စတင်စေခြင်း
if __name__ == '__main__':
    app.run(debug=True)