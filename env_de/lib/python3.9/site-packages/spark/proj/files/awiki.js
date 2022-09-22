dojo.require("dojo.io");
dojo.require("dojo.lfx.*");

function hcontent(word,content){
  var hc = content.replace(/([A-Z]\w+[A-Z]+\w+)\s+/,'<a class="word" href="/ajaxwiki/word/$1">$1</a> ');
  document.getElementById('content').innerHTML = content;
  return hc + '<br /><a class="editr" href="/ajaxwiki/edit/'+word+'">Edit</a>' +
    '<br /><a class="word" href="/ajaxwiki/home">Home</a>';
}
  
function addlink(word){
  var wido = document.getElementById('wido')
  var item = wido.appendChild(document.createElement('a')); 
  if (word == 'new'){
    item.href = '/ajaxwiki/new/';
  }else{
    item.href = '/ajaxwiki/word/'+word;
  }
  item.className = 'word';
  item.innerHTML = word;
  wido.appendChild(document.createElement('br')); 
}

function fireeditor(word){
  var wido = document.getElementById('wido');
  wido.style.display="none";

  var iword,icontent,inew;
  if(typeof(word)=='undefined'){
    iword = '<input type="text" name="word" value="" /><br />';
    icontent = '';
    inew = 'new';
  }else{
    iword = '<input type="hidden" name="word" value="'+word+'" />';
    icontent = document.getElementById('content').innerHTML;
    inew = 'old';
  }

  var tmpdata = document.getElementById('tmpdata');
  tmpdata.innerHTML = '<form id="frmedit" onsubmit="editSave('+
    "'"+inew+"','"+word+"');return false;"+'">'+iword+
    '<textarea id="Editor" name="content">' + icontent +
    '</textarea><br /><input type="submit" value="save" />'+
    '<input type="reset" value="Cancel" onclick="cancelEdit();return false;" /></form>';
  tmpdata.style.display="block";
  return false;
}

function cancelEdit(){
  document.getElementById('wido').style.display="block";
  dojo.lfx.html.highlight("wido", [255, 255, 0], 250).play(1000);
  document.getElementById('tmpdata').innerHTML="";
}

function editSave(oldnew,word){
  var uri;
  if(oldnew == 'new'){ uri = "/ajaxwiki/insert/"+word; }
  else{ uri = "/ajaxwiki/update/"+word; }

  frmnode = document.getElementById("frmedit")
  dojo.io.bind({
    url:uri,
    method:"POST",
    formNode:frmnode,
    load:function(type,data,evt){
      var wido=document.getElementById('wido');
      wido.innerHTML=hcontent(word,document.getElementById('Editor').value);
      wido.style.display="block";
      document.getElementById('tmpdata').style.display="none";
      dojo.lfx.html.highlight("wido", [0, 255, 0], 250).play(1000);
      prepareLinks();
    },
    mimetype:"text/plain",
    encoding: "UTF-8"
  });
}
    
function wowi(node,uri) {
  node.style.display="block";
  dojo.io.bind({
    url:uri,
    handle:function(type,data,evt){
      if(type=='load'){
        var wipeOut = dojo.lfx.wipeOut(node, null, null, function(n) {
          if(uri.match(/^\/ajaxwiki\/home/)){
            n.innerHTML = '';
	    for(var i=0;i<data.length;i++){
              addlink(data[i].word);
            }
            n.appendChild(document.createElement('br')); 
            addlink('new');
          }
          else{ 
            n.innerHTML = hcontent(data.word,data.content);
          }
          dojo.lfx.wipeIn(n).play();
          prepareLinks();
        });
        wipeOut.play();
      }
    },
    mimetype:'text/json'
  });
}

function prepareLinks() {
  if(document.getElementsByTagName){
    var links = document.getElementsByTagName("a");
    for (var i=0; i<links.length; i++) {
      if(links[i].className.match("word")){
        if(links[i].href.match("\/new")){
          links[i].onclick = function(){
            fireeditor();
            return false;
          };
        }else{
          links[i].onclick = function(){
            var uri = this.getAttribute("href");
            wowi(this.parentNode,uri);
            return false;
          };
        }
      }
      if(links[i].className.match("editr")){
        links[i].onclick = function(){
          fireeditor(this.href.split('/').pop())
          return false;
        };
      }
    }
  }
}
