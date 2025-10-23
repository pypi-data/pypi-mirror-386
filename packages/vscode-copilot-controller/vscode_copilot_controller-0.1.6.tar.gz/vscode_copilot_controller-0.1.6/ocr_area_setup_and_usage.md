## Config
- select the entire copilot chat panel
- select the individual buttons or inputs as key areas which are part of the entire chat panel(Set Mode button, Pick Model button, Send button, Chat input, chat display area, interactive buttons area, Keep button, etc)
- provide a dropdown list for the user to select instead of asking the user to write the area name. no need to input area description, just use a default description
- the interactive buttons contains `Continue`, `Allow`, `Enter`, `Yes`, `Try Again`. They usually show up in a certain area in the chat display area.
- dropdown list area select. Set Mode dropdown and Pick Model dropdown. The user needs to click the buttons first before selecting the areas
- area names dropdown options are `chat_panel`, `set_mode_button`, `pick_model_button`, `send_button`, `set_mode_dropdown`, `pick_model_dropdown`, `chat_input`, `chat_display`, `interactive_buttons`, `keep_button`, `chat_display_bottom_text`
- save the config file

## Verify
After the area config, ask the user to move around in the copilot chat panel. The console needs to show where the mouse is, what action the user performs(the cursor hovers on Set Mode button, the Pick Model button is clicked, the cursor hovers on the Chat input, etc). 

## Usage
Provide the following methods
- click_set_mode_button(), this will trigger a dropdown list above the set_mode button for the user to select a mode(Agent, Ask, Edit). 
- set_mode(mode_name), ocr the Set Mode dropdown area and click on the mode_name to complete this operation
- click_pick_model_button(), this will trigger a dropdown list above the pick_model button to select a model(GPT-4.1, GPT-4o, GPT-5 mini, Claude Sonnet 3.5, Claude Sonnet 3.7, Claude Sonnet 4, GPT-5)
- pick_model(model_name), ocr the Pick Model dropdown area and click on the model_name to complete the operation
- input_chat(chat_text)
- send_chat()
- check_keep_button(), ocr is required if the keep button shows in the keep_button area
- click_keep_button()
- check_interactive_button(), ocr is required to detect the type of interactive button in the interactive buttons area. the interactive buttons detection needs to be unit tested with the screenshots in folder [test_screenshots](test_screenshots)
- click_allow_button(), use `Allow|` or `Allow!` or `Allow)` for the allow button in the ocr detection
- click_continue_button(), `Continue` is followed by `Pause`
- click_enter_button()
- click_yes_button(), `Yes` is followed by `No`
- click_try_again_button()
- check_chat_status(), hover the cursor on the send button, a tooltip will show under it. the chat is complete if the tooltip shows `Send`. the chat is in progress if the tooltip shows `Cancel`. You need to ocr the chat_panel that is below the Send button Y position to detect if the tooltip text contains `Send` or `Cancel`. the correct status detecting is to hover on the send button, then it will show a tooltip below the button. you need to ocr the area betwen the send button bottom and the chat panel bottom to check the `Cancel` text or `Send` text.
- scroll_down_chat(), sometimes the chat response doesn't automatically scroll to the bottom. the cursor needs to go to the center of the chat display area to scroll down to the bottom. the indicator of chat bottom is that the `chat_display_bottom_text` shows the model name. ocr this area to make sure it scrolls down to the bottom.
- get_latest_chat_text(), ocr the chat display and return the text.