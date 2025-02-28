def get_settings_html(network_options, nvs):
    # Retrieve saved SSID and password from NVS
    saved_ssid = nvs.get_string("ssid", "")
    saved_password = nvs.get_string("pass", "")

    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Altboard</title>
        <style>
          body {{
            background-color: #111;
            color: #fff;
            font-family: "Times New Roman", Times, serif;
            font-size: 24px;
            position: relative;
            min-height: 100vh;
            margin: 0;
            padding-bottom: 60px;
          }}

          h2,
          #header,
          button {{
            color: #444;
          }}

          h2 {{
            font-weight: 100;
            font-size: 16px;
            text-align: center;
            margin: 0 10px;
          }}

          #header,
          #network {{
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }}

          #network {{
            flex-direction: column;
            width: 60vh;
            margin: 0 auto;
            gap: 10px;
          }}

          #ssid,
          #password {{
            margin-bottom: 5px;
          }}

          button {{
            background-color: #151515;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            font-size: 24px;
          }}

          .line-container {{
            display: flex;
            align-items: center;
            width: 100%;
            margin-top: 40px;
            margin-bottom: 40px;
          }}

          .line {{
            flex-grow: 1;
            border: none;
            border-top: 1px solid #444;
          }}

          #submit-button {{
            position: absolute;
            bottom: 150px;
            left: 50%;
            transform: translateX(-50%);
          }}
        </style>
      </head>
      <body>
        <form id="header" action="/close" method="GET">
          Altboard Settings
          <button type="submit">Close Access Point</button>
        </form>

        <form id="network" action="/submit" method="GET">
          <div class="line-container">
            <hr class="line" />
            <h2>Wi-Fi</h2>
            <hr class="line" />
          </div>

          <div id="ssid">
            <label for="networks">Available Networks:</label>
            <select id="networks" name="networks">
              {network_options}
            </select>
          </div>

          <div id="password">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" value="{saved_password}" />
          </div>

          <div class="line-container">
            <hr class="line" />
            <h2>Pronote</h2>
            <hr class="line" />
          </div>

          <div id="pronote">
            <label for="pronte">Pronte Link:</label>
            <input type="pronte" id="pronte" name="pronte" />
          </div>

          <button type="submit" id="submit-button">Submit</button>
        </form>
      </body>
    </html>
    """

def get_updated_html():
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Settings Updated</title>
        <style>
          body {{
            background-color: #111;
            color: #fff;
            font-family: "Times New Roman", Times, serif;
            font-size: 24px;
            position: relative;
            min-height: 100vh;
            margin: 0;
            padding-bottom: 60px;
          }}

          h1 {{
            text-align: center;
            margin-top: 50px;
            font-weight: 100;
            font-size: 32px;
          }}

          .message {{
            text-align: center;
            font-size: 24px;
            margin: 20px;
          }}

          button {{
            background-color: #151515;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            font-size: 24px;
            display: block;
            margin: 0 auto;
          }}
        </style>
      </head>
      <body>
        <h1>Settings Updated</h1>
        <div class="message">Your Wi-Fi settings have been successfully updated.</div>
        <button onclick="window.location.href='/settings'">Go Back to Settings</button>
      </body>
    </html>
    """ 