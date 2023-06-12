from io import BytesIO
import requests
import pandas as pd
import math






spreadsheet_id = '104XHBWU2Q3dUUYB-OQCt8JcUXiM5vUY0id5KIL49C_4'
file_name = 'https://docs.google.com/spreadsheets/d/{}/export?format=csv'.format(spreadsheet_id)
r = requests.get(file_name)
df = pd.read_csv(BytesIO(r.content))


rows = df.loc[df['user_id'] == 11].iloc[0]
if type(rows['audio']) == float:
    print(rows['audio'])
else:
    print(type(rows['audio']))
# buttons = [
#     InlineKeyboardButton(text=str(idx + 1), callback_data=row[1]['callback'])
#     for idx, row in enumerate(df_sorted.head(3).iterrows())
# ]
#
#
# message_text = f"вы можете выбрать одну из историй героев представленных ниже \n"
# for idx, row in enumerate(rows.iterrows()):
#     print(row[1]['name'])
#     message_text += f'{idx + 1}. {row[1].name} \nО герое: {row[1].about_author}'
#     print(message_text)


