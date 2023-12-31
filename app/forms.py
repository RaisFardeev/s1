from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, TextAreaField, FileField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Email
from . import bcrypt
from .models import User
from flask_wtf.file import FileAllowed


class RegistrationForm(FlaskForm):
    name = StringField('Имя',
                       validators=[DataRequired(), Length(min=1, max=20)],
                       render_kw={"placeholder": "Введите имя"})
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(min=10, max=30)],
                        render_kw={"placeholder": "Введите email"})
    password1 = PasswordField('Пароль',
                              validators=[DataRequired(), Length(min=1, max=20)],
                              render_kw={"placeholder": "Введите пароль"})
    password2 = PasswordField('Повторите пароль',
                              validators=[DataRequired(), Length(min=1, max=20)],
                              render_kw={"placeholder": "Введите пароль еще раз"})
    submit = SubmitField('Зарегестрироваться')

    def validate_email(self, *args):
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors += 'Пользователь с таким адресом уже существует'

    def validate_password(self, *args):
        if self.password1.data != self.password2.data:
            self.password1.errors += 'Пароли не совпадают'


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(min=10, max=30)],
                        render_kw={"placeholder": "Введите email"})
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=1, max=20)],
                             render_kw={"placeholder": "Введите пароль"})
    submit = SubmitField('Log In')

    def validate_(self, *args):
        user = User.query.filter_by(email=self.email.data).first()
        if user is None:
            self.email.errors += 'что-то не так с адресом'
        if not bcrypt.check_password_hash(self.password.data, user.password):
            self.password.errors += 'что-то не так с паролем'


class AdCreateForm(FlaskForm):
    name = StringField('Название',
                       validators=[DataRequired(), Length(max=50)],
                       render_kw={"placeholder": "Введите название"})
    description = TextAreaField('Описание',
                                validators=[DataRequired(), Length(max=300)],
                                render_kw={"placeholder": "Введите описание"})
    category = RadioField('Категория',
                          choices=[('kids', 'Дети'), ('fruits', 'Фрукты'), ('cat3', 'Категория 3')])
    price = IntegerField('Цена',
                         validators=[DataRequired(), NumberRange(min=0)],
                         render_kw={"placeholder": "Введите цену"})
    file_upload = FileField('Файл',
                            validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    submit = SubmitField('Создать')


class AdEditForm(FlaskForm):
    name = StringField('Название',
                       validators=[DataRequired(), Length(max=50)],
                       render_kw={"placeholder": "Введите название"})
    description = TextAreaField('Описание',
                                validators=[DataRequired(), Length(max=300)],
                                render_kw={"placeholder": "Введите описание"})
    category = RadioField('Категория',
                          choices=[('kids', 'Дети'), ('fruits', 'Фрукты'), ('cat3', 'Категория 3')])
    price = IntegerField('Цена',
                         validators=[DataRequired(), NumberRange(min=0)],
                         render_kw={"placeholder": "Введите цену"})
    file_upload = FileField('Файл',
                            validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    submit = SubmitField('Изменить')


class MoneyAddForm(FlaskForm):
    number = IntegerField('Количество денег',
                          validators=[DataRequired(), NumberRange(min=0, max=1000000)],
                          render_kw={"placeholder": "Введите количество денег"})
    submit = SubmitField('Добавить')


class EditProfileForm(FlaskForm):
    name = StringField('Имя',
                       validators=[Length(max=20)],
                       render_kw={"placeholder": "Введите новое имя"})
    email = StringField('Email',
                        validators=[Email(), Length(max=30)],
                        render_kw={"placeholder": "Введите новый email"})
    old_password = PasswordField('Пароль',
                                 validators=[DataRequired(), Length(max=20)],
                                 render_kw={"placeholder": "Введите старый пароль"})
    new_password1 = PasswordField('Пароль',
                                  validators=[Length(max=20)],
                                  render_kw={"placeholder": "Введите новый пароль"})
    new_password2 = PasswordField('Повторите пароль',
                                  validators=[Length(max=20)],
                                  render_kw={"placeholder": "Введите новый пароль еще раз"})
    submit = SubmitField('Редактировать')

    def validate_email(self, *args):
        user = User.query.filter_by(email=self.email.data).first()
        if user is not None and user.email != self.email.data:
            self.email.errors += 'Пользователь с таким адресом уже существует'
        if user.password:
            if not bcrypt.check_password_hash(self.old_password.data, user.password):
                self.old_password.errors.append('что-то не так с паролем')

    def validate_passwords(self, *args):
        if self.new_password1.data != self.new_password2.data:
            self.new_password1.errors.append('Пароли не совпадают')


class ResetPasswordForm1(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(min=10, max=30)],
                        render_kw={"placeholder": "Введите email"})
    submit = SubmitField('Отправить')

    def validate_email(self, *args):
        user = User.query.filter_by(email=self.email.data).first()
        if user is None:
            self.email.errors += 'Пользователь с таким адресом не найден'


class ResetPasswordForm2(FlaskForm):
    password1 = PasswordField('Пароль',
                              validators=[DataRequired(), Length(min=1, max=20)],
                              render_kw={"placeholder": "Введите пароль"})
    password2 = PasswordField('Повторите пароль',
                              validators=[DataRequired(), Length(min=1, max=20)],
                              render_kw={"placeholder": "Введите пароль еще раз"})
    submit = SubmitField('Завершить')

    def validate_password(self, *args):
        if self.password1.data != self.password2.data:
            self.password1.errors += 'Пароли не совпадают'
