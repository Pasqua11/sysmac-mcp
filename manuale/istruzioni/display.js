//----------------------------------------------------
// ヘルプ用JavaScript 2016/12/07  by Hori 
//----------------------------------------------------
$(document).ready(function(){
	
	//----------------------------------------------------
	//2018-07-11 : Hiroshi Hori A-Holic,LLC
	//liststyle_annotation1 のli要素のナンバリング 「Note」
	CheckObj = $('.liststyle_annotation1');
	for (var i = 0; i < CheckObj.length; i ++){
		var Checktmp = CheckObj.eq(i).find('span.num');
		if(Checktmp.length>=2){
			for (var ii = 0; ii < Checktmp.length; ii ++){
				Checktmp.eq(ii).text('' + (1+ii) + '.');
				Checktmp.eq(ii).css('padding-left','0.2em');
			}
		}
	}
	//liststyle_asterisk1 のli要素のナンバリング 「*」
	CheckObj = $('.liststyle_asterisk1');
	for (var i = 0; i < CheckObj.length; i ++){
		var Checktmp = CheckObj.eq(i).find('span.num');
		for (var ii = 0; ii < Checktmp.length; ii ++){
			Checktmp.eq(ii).text(''+(1+ii));
			Checktmp.eq(ii).css('padding-left','0.1em');
		}
	}
	//----------------------------------------------------
	
	//表脚注用のタグの書込
	//$('body').css('display','relative');
	$('body').append('<div id="modal"><!--fn modal--></div>');
	
	
	// 表脚注の表示or非表示
	$('table a').hover(
		function () {
			
			var idName = $(this).attr('href');
			$('div.fn').css('color','#333');
			//対象にhref属性がある場合のみ処理
			if(idName!=''){
				idName = idName.split("#").pop();
				idName = '#'+idName;
				//alert(idName)
				if($(idName).get(0)){
					
					//脚注のポップアップ

					var pos = $(this).position();
					var win = $(window).width();
					var obj = $('#modal');
					obj.html(delelement($(idName).parent('div.fn').html()));
					//中身が無いと表示しない
					if($(idName).parent('div.fn').html()!=null){
						obj.css('display','block');
					}
					obj.css('top',(pos.top + 24) +'px');
					//脚注位置　ウィンドウに対して若干調整
					//bodyのマージンに対してずれるので調整
					var a = $('body').css('margin-left').replace('px','');
					
					obj.css('left',((pos.left - Math.floor(pos.left/win*100)) - a) +'px');
					//各種CSSの調整
					$('#modal div').css({'cssText': 'margin: 0px !important;'});
					$('#modal p').css({'cssText': 'margin: 0px !important;'});
					$('#modal ul').css({'cssText': 'margin: 0px !important;'});
					$('#modal ol').css({'cssText': 'margin: 0px !important;'});
					$('#modal table').css({'cssText': 'margin: 10px 0 0 0 !important; background-color:#fff;'});
					return false;
				}
			}
		},
		function () {
			//脚注消す
			$('#modal').css('display','none');
		}
	);
	$('table a').click(function () {
		//脚注消す
		$('#modal').css('display','none');
		//アンカー位置へのスクロール
		var idName = $(this).attr('href');
		idName = idName.split("#").pop();
		idName = '#'+idName;
		//対象にhref属性がある場合のみ処理
		if(idName!=''){
			if($(idName).get(0)){
				$(idName).parent('div.fn').css('color','#f00');
				scrollmenu(idName);
				return false;
			}
		}
	});
	
	//表の右端を非表示にする
	// colを非表示
	var tableclassName = '.rightcell_no';
	var tempObj = $('table' + tableclassName);
	for (var i = 0; i < tempObj.length; i ++){
		var chObj = tempObj.eq(i).find('col');
		chObj.eq(chObj.length-1).css({'display':'none'});
	}
	// td、thを非表示
	var tempObj = $('table' + tableclassName +' tr');
	for (var i = 0; i < tempObj.length; i ++){
		
		if(tempObj.eq(i).find('td').length){
			var chObj = tempObj.eq(i).find('td');
			chObj.eq(chObj.length-1).css({'display':'none'});
		}else{
			var chObj = tempObj.eq(i).find('th');
			chObj.eq(chObj.length-1).css({'display':'none'});
		}
		if(chObj.eq(chObj.length-1).attr('rowspan')){
			i += Number(chObj.eq(chObj.length-1).attr('rowspan')) - 1;
		}
	}
	
});

//----------------------------------------------------
//スクロール用
//----------------------------------------------------
function scrollmenu(idName){
	idName = '#'+idName.split('#')[1];
	$('html,body').animate({
		scrollTop:$(idName).offset().top-60
	},{
		duration:'slow',
		complete: function() {
			colDel(1500);
		}
	});
	return false;
}
//----------------------------------------------------
//タイマー
//----------------------------------------------------
function colDel(num){
	setTimeout(function(){
		$('div.fn').css('color','#333');
	},num);
}
//----------------------------------------------------
//表脚注用の最初のAタグ削除
//----------------------------------------------------
function delelement(in_str){
	if(in_str!=null){
		in_str = in_str.split('</A>').join('</a>');
		var temp = in_str.split('</a>');
		temp.shift();
		return(temp.join('</a>'));
	}
}
