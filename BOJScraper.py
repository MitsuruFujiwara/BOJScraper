import pandas as pd
import numpy as np
from selenium import webdriver

class BOJScraper(object):
    """
    日本銀行の時系列統計データ検索サイトからデータを自動取得するためのスクリプト
    http://www.stat-search.boj.or.jp/index.html
    """

    def __init__(self, driverpath='chromedriver', currency='USD', addDateFlag=False):
        self.url = 'http://www.stat-search.boj.or.jp/ssi/cgi-bin/famecgi2?cgi=$nme_a000&lstSelection=FM08'
        self.driverpath = driverpath
        self.addDateFlag = addDateFlag
        self.currency = currency # 'USD' or 'EUR'
        self.datalistUSD = [
        '東京市場　ドル・円　スポット　9時時点',
        '東京市場　ドル・円　スポット　最高値',
        '東京市場　ドル・円　スポット　最安値',
        '東京市場　ドル・円　スポット　17時時点',
        '東京市場　ドル・円　スポット　中心相場',
        '東京市場　ドル・円　スポット出来高',
        '東京市場　ドル・円　スワップ出来高']
        self.datalistEUR = [
        '東京市場　ユーロ・ドル　スポット　9時時点',
        '東京市場　ユーロ・ドル　スポット　最高値',
        '東京市場　ユーロ・ドル　スポット　最安値',
        '東京市場　ユーロ・ドル　スポット　17時時点',
        '東京市場　ユーロ・ドル　スポット出来高',
        '東京市場　ユーロ・ドル　スワップ出来高']

    def reshapeData(self, url_csv, datalist):
        # urlからデータをロード
        df = pd.read_csv(url_csv)

        # 不要な行を削除
        df = df[1:]

        # カラム名を変更
        col = ['date'] + datalist
        df.columns = col

        # インデックスにdateを指定
        df.index = pd.to_datetime(df.date)
        df = df.drop('date', axis=1)

        # 欠損値をnanに変換
        df = df.replace('NA    ', np.nan).replace('NA   ', np.nan)

        # 欠損値を削除
        df = df.dropna()

        # データ型をfloatに指定
        df = df.astype('float')

        # 日付のフラグを追加
        if self.addDateFlag:
            dateFlag = self.getDateFlag(df.index)
            df = pd.concat([df, dateFlag], axis=1)

        return df

    def getDateFlag(slef, df_date):

        # datetime型の日付データを取得
        df_date = pd.to_datetime(df_date)

        # 日付のフラグ
        _day = pd.get_dummies(df_date.day, drop_first=True, prefix='day_').astype(int)

        # 月のフラグ
        _month = pd.get_dummies(df_date.month, drop_first=True, prefix='month_').astype(int)

        # 曜日のフラグ
        _weekday = pd.get_dummies(df_date.weekday, drop_first=True, prefix='weekday_').astype(int)

        # 年の何週目かのフラグ
        _weekofyear = pd.get_dummies(df_date.weekofyear, drop_first=True, prefix='weekofyear_').astype(int) #年の何週目か

        # ダミー変数を結合
        dateFlag = pd.concat([_day, _month, _weekday, _weekofyear],axis=1)

        # indexを日付に変更
        dateFlag.index = df_date

        return dateFlag

    def getData(self, fromYear, toYear):
        if self.currency=='USD':
            datalist=self.datalistUSD
            tmp_i = 0
        elif self.currency=='EUR':
            datalist=self.datalistEUR
            tmp_i = 7

        # driverを定義
        driver = webdriver.Chrome(self.driverpath)

        # urlを取得
        driver.get(self.url)

        # 外国為替相場状況（日次）を選択
        driver.find_element_by_class_name('selectedMenu').click()

        # "展開"ボタンをクリック
        driver.find_element_by_xpath('/html/body/div[2]/div/ul[2]/li[1]/div[1]/div[1]/div[2]/input').click()

        # データ項目のチェックボックスにチェックを入れる
        for i, t in enumerate(datalist):
            i += tmp_i
            _i = str(i+1)
            path = '//*[@id="menuSearchDataCodeList"]/tbody/tr[' + _i +']/td/label'
            driver.find_element_by_xpath(path).click()

        # "抽出条件に追加"ボタンを押す
        driver.find_element_by_xpath('/html/body/div[2]/div/ul[2]/li[1]/div[1]/div[2]/div[4]/a').click()

        # 取得するデータの期間を入力
        driver.find_element_by_id('fromYear').send_keys(fromYear)
        driver.find_element_by_id('toYear').send_keys(toYear)

        # "抽出"ボタンを押す
        driver.find_element_by_xpath('//*[@id="resultArea"]/div[4]/div[1]/a[1]').click()

        # "抽出結果"ウインドウへ移動
        window_res = driver.window_handles[1]
        driver.switch_to.window(window_res)

        # "ダウンロード"ボタンを押す
        driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/table/tbody/tr[2]/td[4]').click()

        # "ダウンロード"ウインドウへ移動
        window_dl = driver.window_handles[2]
        driver.switch_to.window(window_dl)

        # ダウンロードするcsvファイルのurlを取得
        url_csv = driver.find_element_by_css_selector('body > div.contents > div > div > center > div > table > tbody > tr > td > a').get_attribute('href')

        # データを加工
        df = self.reshapeData(url_csv, datalist)

        # driverを閉じる
        driver.quit()

        return df

if __name__ == '__main__':
    # test
    bojs = BOJScraoer()
    df = bojs.getData(2017, 2017)
    print(df)
