# GDG on Campus: PTIT — phát triển local

Website DMOJ với navbar đen, logo/favicon GDG PTIT, GitLab Sans và Geist Mono.
Repository máy chấm: https://github.com/gdgocptit/judge-server.

Cần Docker/OrbStack, Homebrew, Node/npm, uv và Xcode Command Line Tools.
Chạy từ thư mục gốc repository website:

```sh
docker compose -f dev/compose.yml up -d --wait
brew install mysql-client pkg-config gettext
export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export PATH="$(brew --prefix gettext)/bin:$PATH"
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt mysqlclient 'redis<6' websocket-client setuptools
cp -n dev/local_settings.example.py dmoj/local_settings.py
mkdir -p .local/static .local/media .local/problems
source .venv/bin/activate
git submodule update --init --recursive
npm ci
npm install --no-save --package-lock=false sass postcss-cli@11 postcss autoprefixer
PATH="$PWD/node_modules/.bin:$PATH" ./make_style.sh
python manage.py check
python manage.py migrate
python manage.py loaddata navbar language_all
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py compilemessages
python manage.py compilejsi18n
python manage.py runserver 127.0.0.1:8000
```

Mở http://127.0.0.1:8000/ và `/admin/`. Database mới, không chứa dữ liệu hay
tài khoản production. Email in ra terminal; đăng ký công khai tắt.
Sau khi sửa SCSS, chạy lại `make_style.sh` với PATH như trên.

Tác vụ nền cần terminal riêng, đã kích hoạt `.venv`:

```sh
celery -A dmoj_celery worker --pool=solo --loglevel=INFO
```

Cấu hình này dành cho phát triển web. Chấm bài cần Linux VM/container,
bridge, runtime và judge key riêng; chưa được khởi chạy bởi Compose trên.
Xem tài liệu upstream và repository máy chấm để thiết lập phần này.
Không dùng cấu hình hay mật khẩu local cho production.

Đã kiểm tra cú pháp cấu hình. Chưa cài dependency/chạy ứng dụng trên macOS.
