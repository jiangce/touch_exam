require([
    "dojox/mobile/parser",
    "dojo/dom",
    "dojo/dom-construct",
    "dojo/dom-style",
    "dijit/registry",
    "dojo/request",
    "dojo/_base/lang",
    "dojox/mobile/ListItem",
    "dojox/mobile/RadioButton",
    "dojox/mobile/CheckBox",
    "dojox/mobile",
    "dojox/mobile/compat",
    "dojo/domReady!",
    "dojox/mobile/ScrollableView",
    "dojox/mobile/Heading",
    "dojox/mobile/RoundRectList",
    "dojox/mobile/Switch",
    "dojox/mobile/RoundRect",
    "dojox/mobile/ToolBarButton"], function (parser, dom, domConstruct, domStyle, registry, request, lang, ListItem, RadioButton, CheckBox) {

    onstart = function () {
        setting = {
            hassingle: registry.byId('setting_single').value,
            hasmultiple: registry.byId('setting_multiple').value,
            hastorf: registry.byId('setting_trueorfalse').value,
            easy: registry.byId('setting_easy').value,
            normal: registry.byId('setting_normal').value,
            hard: registry.byId('setting_hard').value,
            onlywrong: registry.byId('setting_onlywrong').value
        };
        request.post('/getquestion/', {data: setting, handleAs: 'json'})
            .then(lang.hitch(this, function (timu) {
            lang.hitch(this, initExercisePage)(timu);
        }),
            function (err) {
                alert("服务器响应失败，请重试");
            });
    };

    onnext = function () {
        var question = registry.byId('exercise_question');
        if (question.doneflag) {
            lang.hitch(this, onstart)();
        }
        else {
            oncommit();
            setTimeout(lang.hitch(this, onstart), 2000);
        }
    };

    var diff = {1: '容易', 2: '中等', 3: '困难'};

    function initExercisePage(timu) {
        if (!timu) {
            alert('无可选题目');
            return;
        }
        domStyle.set(dom.byId('correct'), 'visibility', 'hidden');
        domStyle.set(dom.byId('wrong'), 'visibility', 'hidden');
        removeChoices();
        registry.byId('exercise_title').set('label', timu.type + "(" + diff[timu.diff] + ")");
        var question = registry.byId('exercise_question');
        question.containerNode.innerText = timu.question;
        question.question = timu._id;
        question.doneflag = false;
        var choices = registry.byId('choices');
        for (var i = 0; i < timu.choice.length; i++) {
            var choice_item = new ListItem({id: 'choice_item' + i, class: 'choice'});
            choice_item.answer = timu.answer.indexOf(i) != -1;
            choices.addChild(choice_item);
            var choice_button;
            if (timu.type == '多选') {
                choice_button = new CheckBox({id: 'choice_button' + i});
            } else {
                choice_button = new RadioButton({id: 'choice_button' + i, name: 'question'});
            }
            choice_item.addChild(choice_button);
            domConstruct.create('label',
                {
                    id: 'choice_label' + i,
                    for: 'choice_button' + i,
                    innerHTML: timu.choice[i]
                }, choice_item.containerNode);
        }
        this.transitionTo("page_exercise");
    }

    function removeChoices() {
        for (var i = 0; ; i++) {
            var button = registry.byId('choice_button' + i);
            if (!button) {
                break;
            }
            button.destroy();
        }
        for (i = 0; ; i++) {
            var item = registry.byId('choice_item' + i);
            if (!item) {
                break;
            }
            item.destroy();
        }
    }

    oncommit = function () {
        var question = registry.byId('exercise_question');
        if (question.doneflag) {
            return;
        }
        question.doneflag = true;
        var result = showAnswerAndCheck();
        var image = result ? 'correct' : 'wrong';
        domStyle.set(dom.byId(image), 'visibility', 'visible');
        if (result) {
            request.post('/commitcorrect/', {data: {correctid: question.question}});
        } else {
            request.post('/commitwrong/', {data: {wrongid: question.question}});
        }
    };

    function showAnswerAndCheck() {
        var result = true;
        for (var i = 0; ; i++) {
            var item = registry.byId('choice_item' + i);
            if (!item) {
                break;
            }
            result = result && (item.answer == registry.byId('choice_button' + i).get('checked'));
            item.set('selected', item.answer);
        }
        return result;
    }

    parser.parse();
});