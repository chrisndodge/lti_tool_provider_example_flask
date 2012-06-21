from flask import Flask, render_template, session, request,\
        redirect, url_for, make_response
        
from ims_lti_py import ToolProvider

from time import time

app = Flask(__name__)
app.secret_key = '\xc8K\x80\x00e}R\x92I\x1b\xec\x10"oP\xc5o~~\x83\xb6f\x9e4'

oauth_creds = { 'test': 'secret', 'testing': 'supersecret' }

@app.route('/', methods = ['GET'])
def index():
    render_template('index.html')

@app.route('/lti_tool', methods = ['POST'])
def lti_tool():
    key = request.form.get('oauth_consumer_key')
    if key:
        secret = oauth_creds.get(key)
        if secret:
            tool_provider = ToolProvider(key, secret, request.form)
        else:
            tool_provider = ToolProvider(None, None, request.form)
            tool_provider.lti_msg = 'Your consumer didn\'t use a recognized key'
            tool_provider.lti_errorlog = 'You did it wrong!'
            return render_template('error.html', message = 'Consumer key wasn\'t recognized')
    else:
        return render_template('error.html', message = 'No consumer key')

    if not tool_provider.is_valid_request(request):
        return render_template('error.html', 'The OAuth signature was invalid')

    if time() - tool_provider.request_oauth_timestamp > 60*60:
        return render_template('error.html', message = 'Your request is too old.')

    # This does truly check anything, it's just here to remind you  that real
    # tools should be checking the OAuth nonce
    if was_nonce_used_in_last_x_minutes(tool_provider.request_oauth_nonce, 60):
        return render_template('error.html', message = 'Why are you reusing the nonce?')

    session['launch_params'] = tool_provider.to_params
    username = tool_provider.username('Dude')
    if tool_provider.is_outcome_service():
        return render_template('assessment', username =  username)
    else:
        tool_provider.lti_msg = 'Sorry that you tool was so lame.'
        return render_template('boring_tool',
                username = username,
                student = tool_provider.is_student(),
                instructor = tool_provider.is_teacher(),
                roles = tool_provider.roles,
                launch_presentation_return_url =\
                        tool_provider.launch_presentation_return_url)

@app.route('/assessment', methods = ['POST'])
def assessment():
    if session['launch_params']:
        key = session['launch_params']['oauth_consumer_key']
    else:
        return render_template('error.html', message = 'The tool never launched')

    tool_provider = ToolProvider(key, oauth_creds[key],
            session['launch_params'])

    if tool_provider.is_outcome_service():
        return render_template('error.html', 'The tool wasn\'t launch as an outcome service.')

    # Post the given score to the ToolConsumer
    response = tool_provider.post_replace_result(request.form.get('score'))
    if response.is_success():
        score = request.form.get('score')
        tool_provider.lti_message = 'Message shown when arriving back at Tool Consumer.'
        return render_template('assessment_finished.html',
                score = score)
    else:
        tool_provider.lti_errormsg = 'The Tool Consumer failed to add the score.'
        return render_template('error.html', message = response.description)

@app.route('/tool_config.xml' methods = ['GET'])
def tool_config():
    # TODO

def was_nonce_used_in_last_x_minutes(nonce, minutes):
    # TODO: Implement something here
    return False 

if __name__ == '__main__':
    app.run()
