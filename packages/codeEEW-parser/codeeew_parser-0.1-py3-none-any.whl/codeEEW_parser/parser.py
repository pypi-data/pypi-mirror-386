import json
 
def parse_data(data):
    json_dict = {}
    json_dict["issue"] = {}
    json_dict["earthquake"] = {}
    json_dict["earthquake"]["hypocenter"] = {}
    json_dict["accuracy"] = {}
    json_dict["area"] = []
    # ヘッダー部分
    ## 電文種別
    type = data[0:2]
    match type:
        case "35":
            json_dict["type"] = "最大予測震度のみの緊急地震速報"
        case "36":
            json_dict["type"] = "Ｍ、最大予測震度及び主要動到達予測時刻の緊急地震速報"
        case "37":
            json_dict["type"] = "Ｍ、最大予測震度及び主要動到達時刻の緊急地震速報"
        case "38":
            json_dict["type"] = "テスト電文"
        case "39":
            json_dict["type"] = "キャンセル（取り消し）情報"
        case "47":
            json_dict["type"] = "般向け緊急地震速報"
        case "48":
            json_dict["type"] = "キャンセル報"
        case "61":
            json_dict["type"] = "リアルタイム震度電文（工学的基盤面の値）、リアルタイム震度電文のキャンセル報"
    ## 発信官署
    source = data[3:5]
    match source:
        case "1":
            json_dict["issue"]["source"] = "札幌"
        case "2":
            json_dict["issue"]["source"] = "仙台"
        case "3":
            json_dict["issue"]["source"] = "東京"
        case "4":
            json_dict["issue"]["source"] = "大阪"
        case "5":
            json_dict["issue"]["source"] = "福岡"
    ## 電文の種類
    telegram_type = data[6:8]
    match telegram_type:
        case "00":
            json_dict["issue"]["telegram_type"] = "通常"
        case "01":
            json_dict["issue"]["telegram_type"] = "訓練"
        case "10":
            json_dict["issue"]["telegram_type"] = "通常の取り消し"
        case "11":
            json_dict["issue"]["telegram_type"] = "訓練の取り消し"
        case "20":
            json_dict["issue"]["telegram_type"] = "参考情報またはテスト電文"
        case "30":
            json_dict["issue"]["telegram_type"] = "コード部全体の配信試験"
    ## 電文発信時刻
    outgoing_time_moto = data[9:21]
    outgoing_time = "20" + outgoing_time_moto[0:2] + "-" + outgoing_time_moto[2:4] + "-" + outgoing_time_moto[4:6]
    outgoing_time = outgoing_time + " " + outgoing_time_moto[6:8] + ":" + outgoing_time_moto[8:10] + ":" + outgoing_time_moto[10:12]
    json_dict["issue"]["outgoing_time"] = outgoing_time
    # 電文の内容
    body = data[26:]
    ## 警報の種類(予報:0 警報:1 不明または取り消し:2)
    match body[96]:
        case "0":
            json_dict["issue"]["warning"] = False
        case "1":
            json_dict["issue"]["warning"] = True
        case _:
            json_dict["issue"]["warning_type"] = False
    ## 発生時刻(PLUMの場合は検知時刻)
    occurrence_time_moto = body[0:12]
    occurrence_time = "20" + occurrence_time_moto[0:2] + "-" + occurrence_time_moto[2:4] + "-" + occurrence_time_moto[4:6]
    occurrence_time = occurrence_time + " " + occurrence_time_moto[6:8] + ":" + occurrence_time_moto[8:10] + ":" + occurrence_time_moto[10:12]
    json_dict["earthquake"]["occurrence_time"] = occurrence_time
    ## EventId
    eventid = body[15:29]
    json_dict["issue"]["EventID"] = eventid
    ## 最終報か
    isFinal = body[33]
    match isFinal:
        case "9":
            json_dict["issue"]["isFinal"] = True
        case _:
            json_dict["issue"]["isFinal"] = False
    ## 予測手法
    isPLUM = body[96]
    if isPLUM == 9:
        json_dict["issue"]["isPLUM"] = True
    else:
        json_dict["issue"]["isPLUM"] = False
    ## 震央コード
    hypocenter_code = body[60:63]
    if hypocenter_code == "///":
        json_dict["earthquake"]["hypocenter"]["code"] = "不明"
        json_dict["issue"]["isCancelled"] = True
    else:
        json_dict["earthquake"]["hypocenter"]["code"] = hypocenter_code
        json_dict["issue"]["isCancelled"] = False
    ## n報(99以上は非対応)
    serial = body[34:36]
    json_dict["issue"]["Serial"] = serial
    ## 震源の経緯度(南緯・西経の場合は-になる)
    hypocenter_lat = body[64:68]
    hypocenter_lon = body[69:74]
    match hypocenter_lat[0]:
        case "N":
            json_dict["earthquake"]["hypocenter"]["lat"] = str(float(hypocenter_lat[1:]) / 10)
        case "S":
            json_dict["earthquake"]["hypocenter"]["lat"] = str(-float(hypocenter_lat[1:]) / 10)
        case _:
            json_dict["earthquake"]["hypocenter"]["lat"] = "不明"
    match hypocenter_lon[0]:
        case "E":
            json_dict["earthquake"]["hypocenter"]["lon"] = str(float(hypocenter_lon[1:]) / 10)
        case "W":
            json_dict["earthquake"]["hypocenter"]["lon"] = str(-float(hypocenter_lon[1:]) / 10)
        case _:
            json_dict["earthquake"]["hypocenter"]["lat"] = "不明"
    ## 深さ(仮定震源要素の場合は10固定)
    if body[75:78] == "///":
        depth = "不明"
    else:
        depth = str(int(body[75:78]) * 1)
    json_dict["earthquake"]["hypocenter"]["depth"] = depth
    ## マグニチュード(仮定震源要素の場合は1.0固定)
    if body[79:81] == "//":
        magnitude = "不明"
    else:
        magnitude = str(float(body[79:81]) / 10)
    json_dict["earthquake"]["hypocenter"]["magnitude"] = magnitude
    ## 震度(文字型 5+,5-など)
    maxScale = body[82:84]
    json_dict["earthquake"]["maxScale"] = shindo_henkan(maxScale)
    ## データの精度
    accuracy = body[87:91]
    hyp_accuracy = accuracy[0]
    dep_accuracy = accuracy[1]
    mag_accuracy = accuracy[2]
    mag_station = accuracy[3]
    ### 震央精度
    match hyp_accuracy:
        case "1":
            json_dict["accuracy"]["hypocenter"] = "P 波／S 波レベル越え、IPF 法（1 点）、または仮定震源要素"
        case "2":
            json_dict["accuracy"]["hypocenter"] = "IPF 法（2 点）"
        case "3":
            json_dict["accuracy"]["hypocenter"] = "IPF 法（3 点／4 点）"
        case "4":
            json_dict["accuracy"]["hypocenter"] = "IPF 法（5 点以上）"
        case "5":
            json_dict["accuracy"]["hypocenter"] = "防災科研システム（4 点以下、または精度情報なし）"
        case "6":
            json_dict["accuracy"]["hypocenter"] = "防災科研システム（5 点以上）"
        case "7":
            json_dict["accuracy"]["hypocenter"] = "EPOS（海域〔観測網外〕）"
        case "8":
            json_dict["accuracy"]["hypocenter"] = "EPOS（内陸〔観測網内〕）"
        case "9":
            json_dict["accuracy"]["hypocenter"] = "予備"
        case _:
            json_dict["accuracy"]["hypocenter"] = "不明、未設定時、キャンセル時"
    ### 深さ精度
    match dep_accuracy:
        case "1":
            json_dict["accuracy"]["depth"] = "P 波／S 波レベル越え、IPF 法（1 点）、または仮定震源要素"
        case "2":
            json_dict["accuracy"]["depth"] = "IPF 法（2 点）"
        case "3":
            json_dict["accuracy"]["depth"] = "IPF 法（3 点／4 点）"
        case "4":
            json_dict["accuracy"]["depth"] = "IPF 法（5 点以上）"
        case "5":
            json_dict["accuracy"]["depth"] = "防災科研システム（4 点以下、または精度情報なし）"
        case "6":
            json_dict["accuracy"]["depth"] = "防災科研システム（5 点以上）"
        case "7":
            json_dict["accuracy"]["depth"] = "EPOS（海域〔観測網外〕）"
        case "8":
            json_dict["accuracy"]["depth"] = "EPOS（内陸〔観測網内〕）"
        case "9":
            json_dict["accuracy"]["depth"] = "予備"
        case _:
            json_dict["accuracy"]["depth"] = "不明、未設定時、キャンセル時"
    ### マグニチュード精度
    match mag_accuracy:
        case "1":
            json_dict["accuracy"]["magnitude"] = "未定義"
        case "2":
            json_dict["accuracy"]["magnitude"] = "防災科研システム 〔防災科研Hi-net データ〕"
        case "3":
            json_dict["accuracy"]["magnitude"] = "全点P 相"
        case "4":
            json_dict["accuracy"]["magnitude"] = "P 相／全相混在"
        case "5":
            json_dict["accuracy"]["magnitude"] = "全点全相"
        case "6":
            json_dict["accuracy"]["magnitude"] = "EPOS"
        case "7":
            json_dict["accuracy"]["magnitude"] = "未定義"
        case "8":
            json_dict["accuracy"]["magnitude"] = "P 波／S 波レベル越え、または仮定震源要素"
        case "9":
            json_dict["accuracy"]["magnitude"] = "予備"
        case _:
            json_dict["accuracy"]["magnitude"] = "不明、未設定時、キャンセル時"
    ### マグニチュード使用観測点数（※気象庁の部内システムでの利用）
    match mag_station:
        case "1":
            json_dict["accuracy"]["magnitude_station"] = "1 点、P 波／S 波レベル越え、または仮定震源要素"
        case "2":
            json_dict["accuracy"]["magnitude_station"] = "2 点"
        case "3":
            json_dict["accuracy"]["magnitude_station"] = "3 点"
        case "4":
            json_dict["accuracy"]["magnitude_station"] = "4 点"
        case "5":
            json_dict["accuracy"]["magnitude_station"] = "5 点以上"
        case "/":
            json_dict["accuracy"]["magnitude_station"] = "不明、未設定時、キャンセル時"
        case _:
            json_dict["accuracy"]["magnitude_station"] = "未使用"
    ## 海域か陸域("land" or "sea" or "unknown")
    sea_or_land = body[95]
    match sea_or_land:
        case "0":
            json_dict["earthquake"]["sea_or_land"] = "land"
        case "1":
            json_dict["earthquake"]["sea_or_land"] = "sea"
        case _:
            json_dict["earthquake"]["sea_or_land"] = "unknown"
    ## 推定最大震度の変化
    maxScale_change = body[103]
    match maxScale_change:
        case "0":
            json_dict["earthquake"]["maxScale_change"] = "ほとんど変化なし"
        case "1":
            json_dict["earthquake"]["maxScale_change"] = "最大予測震度が1.0 以上大きくなった。"
        case "2":
            json_dict["earthquake"]["maxScale_change"] = "最大予測震度が1.0 以上小さくなった。"
        case "/":
            json_dict["earthquake"]["maxScale_change"] = "不明、未設定時、キャンセル時"
        case _:
            json_dict["earthquake"]["maxScale_change"] = "未定義"
    ## 推定最大震度の変化理由
    maxScale_change_reason = body[104]
    match maxScale_change_reason:
        case "0":
            json_dict["earthquake"]["maxScale_change_reason"] = "変化なし"
        case "1":
            json_dict["earthquake"]["maxScale_change_reason"] = "主としてＭが変化したため(1.0 以上)。"
        case "2":
            json_dict["earthquake"]["maxScale_change_reason"] = "主として震源位置が変化したため(10.0km 以上)。"
        case "3":
            json_dict["earthquake"]["maxScale_change_reason"] = "Ｍ及び震源位置が変化したため(1 と2 の複合条件)。"
        case "4":
            json_dict["earthquake"]["maxScale_change_reason"] = "震源の深さが変化したため。"
        case "9":
            json_dict["earthquake"]["maxScale_change_reason"] = "PLUM 法による予測により変化したため。"
        case "/":
            json_dict["earthquake"]["maxScale_change_reason"] = "不明、未設定時、キャンセル時"
        case _:
            json_dict["earthquake"]["maxScale_change_reason"] = "未定義"
    # 地域ごとの予測震度
    yosoushindo = data[139:]
    yosoushindo_items = int((len(data) - 144) / 20)
    for i in range(yosoushindo_items):
        yosoushindo_temp = yosoushindo[i*20:i*20+20]
        yosoushindo_json = {}
        ## 震央コード
        yosoushindo_hypocenter_code = yosoushindo_temp[0:3]
        yosoushindo_json["code"] = yosoushindo_hypocenter_code
        ## 最大予測震度
        yosoushindo_from = yosoushindo_temp[7:9]
        yosoushindo_to = yosoushindo_temp[5:7]
        if yosoushindo_temp == "//":
            yosoushindo_json["From"] = shindo_henkan(yosoushindo_to)
            yosoushindo_json["To"] = "over"
        else:
            yosoushindo_json["From"] = shindo_henkan(yosoushindo_from)
            yosoushindo_json["To"] = shindo_henkan(yosoushindo_to)
        ## 到達予想
        yosoushindo_arrival_time = yosoushindo_temp[10:16]
        if yosoushindo_arrival_time == "//////":
            yosoushindo_json["arrival_time"] = "//////"
        else:
            yosoushindo_arrival_time = yosoushindo_arrival_time[0:2] + ":" + yosoushindo_arrival_time[2:4] + ":" + yosoushindo_arrival_time[4:6]
            yosoushindo_json["arrival_time"] = yosoushindo_arrival_time
        ## 警報状況と到達予測状況
        yosoushindo_warning_and_status = yosoushindo_temp[17:19]
        yosoushindo_warning = yosoushindo_warning_and_status[0:1]
        yosoushindo_status = yosoushindo_warning_and_status[1:]
        match yosoushindo_warning:
            case "1":
                yosoushindo_json["warning"] = True
            case _:
                yosoushindo_json["warning"] = False
        match yosoushindo_status:
            case "0":
                yosoushindo_json["status"] = "未到達"
            case "1":
                yosoushindo_json["status"] = "既に到達と予測"
            case "9":
                yosoushindo_json["status"] = "主要動到達時刻の予測なし（PLUM 法による予測）"
            case _:
                yosoushindo_json["status"] = "不明"
        ## 配列として予想震度を追加
        json_dict["area"].append(yosoushindo_json)
    # jsonを返す
    return json.dumps(json_dict, ensure_ascii=False)
 
def shindo_henkan(data):
    if data == "//":
            shindo = "不明"
    else:
        if data == "01" or data == "02" or data == "03" or data == "04" or data == "07":
            shindo = str(int(data) * 1)
        else:
            shindo = data
    return shindo
 