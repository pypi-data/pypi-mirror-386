# codeEEW_parser
緊急地震速報のコード電文をjson形式にパースするPythonのパッケージです。

## 動作等について
動作の保証は一切ありません。**利用者の自己責任**で使用してください。    
次の場合は正しく動作しません。
- コード電文が分割されているとき
- EEWが100報を超えるとき
- 予測震度部分が EBI ではないとき

## 戻り値のjsonの形式
| 要素名 | 型 | 内容 | 取り得る値 |
|--------|------|------|-------------|
| type | string | 情報のタイトル | [typeの取り得る値](./取り得る値.md#typeの取り得る値)を参照 |
| issue.telegram_type | string | 電文のタイプ | [telegram_typeの取り得る値](./取り得る値.md#telegram_typeの取り得る値)を参照 |
| issue.outgoing_time | string | 電文の発信時刻 | YYYY-MM-DD HH:MM:SS |
| issue.warning | bool | 警報が発表されているか | true / false |
| issue.EventID | string | EventId | 14文字の半角数字 |
| issue.isFinal | bool | この電文が最終報か | true / false |
| issue.isPLUM | bool | この電文がPLUM法によるものか | true / false |
| issue.isCancelled | bool | この電文がキャンセル報か | true / false |
| issue.Serial | string | 電文のn報 | 半角数字 |
| earthquake.hypocenter.code | string | 震央コード | 3桁の半角数字 または "不明" |
| earthquake.hypocenter.lat | string | 緯度(南緯はマイナスとなる) | 小数点以下一桁までの緯度 または "不明" |
| earthquake.hypocenter.lon | string | 経度(西経はマイナスとなる) | 小数点以下一桁までの経度 または "不明" |
| earthquake.hypocenter.depth | string | 深さ | 2-3桁の半角数字 または "不明" |
| earthquake.hypocenter.magnitude | string | マグニチュード | 小数点一桁までのマグニチュード または "不明" |
| earthquake.occurrence_time | string | 発生時刻(PLUM法の場合は検知時刻) | YYYY-MM-DD HH:MM:SS |
| earthquake.maxScale | string | 最大震度 | 1,2,3,4,5-,5+,6-,6+,7 または "不明" |
| earthquake.sea_or_land | string | 海域か陸域 | "sea" または "land" または "unknown" |
| earthquake.maxScale_change | string | 推定最大震度の変化 | [maxScale_changeの取り得る値](./取り得る値.md#maxScale_changeの取り得る値)を参照 |
| earthquake.maxScale_change_reason | string | 推定最大震度の変化 | [maxScale_change_reasonの取り得る値](./取り得る値.md#maxScale_change_reasonの取り得る値)を参照 |
| accuracy.hypocenter | string | 震央の確からしさ | [accuracyの取り得る値1](./取り得る値.md#accuracyの取り得る値1)を参照 |
| accuracy.depth | string | 震源の深さの確からしさ | [accuracyの取り得る値1](./取り得る値.md#accuracyの取り得る値1)を参照 |
| accuracy.magnitude | string | マグニチュードの確からしさ | [accuracyの取り得る値2](./取り得る値.md#accuracyの取り得る値2)を参照 |
| accuracy.magnitude_station | string | マグニチュード使用観測点数(非推奨) | [コード電文解説資料](https://www.data.jma.go.jp/suishin/shiyou/pdf/no40202)のP15を参照 |
| area | array | 予想震度 | 震央地名ごとの予測震度(震度4以上) |
| area.code | string | 震央コード | 3桁の半角数字 |
| area.From | string | 予測震度の下限 | 1,2,3,4,5-,5+,6-,6+,7 |
| area.To | string | 予測震度の上限 | 1,2,3,4,5-,5+,6-,6+,7 または "over" |
| area.arrival_time | string | 主要動の到達予想時刻<br>(PLUM法:その震度を予測した時刻) | HH:MM:SS または "//////" |
| area.warning | bool | 警報が発表されているか | true / false |
| area.status | string | 主要動の到達予測状況 | [statusの取り得る値](./取り得る値.md#statusの取り得る値)を参照 |

## jsonの補足
### マグニチュード使用観測点数(非推奨)について
マグニチュード使用観測点数は解説資料に「気象庁の部内システムでの利用」との表記があります。  
使用することは推奨されません。
