# get-slackid-kotid

SlackからKing of Timeシステムへコマンドで打刻するシステム（通称、kotアプリ）を  
自動メンテナンスするためのコードです。  
定期実行すること前提とし、Slack IDが設定されていなければ、Slack IDと  
King of Time内のEmployee IDを取得し、自動設定します。  