(function(){
  var D=JSON.parse(document.getElementById("chart-data").textContent);
  var NS="http://www.w3.org/2000/svg";
  function el(t,a,txt){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e;}
  function tip(e,s){e.appendChild(el("title",{},s));return e;}
  function fmt(n){if(n>=1e6){var v=n/1e6,d=Number.isInteger(v)?0:(v>=10?1:2);return v.toFixed(d).replace(".",",")+"M";}if(n>=1e3)return Math.round(n/1e3).toLocaleString("es-ES")+"K";return String(Math.round(n));}
  function full(n){return Math.round(n).toLocaleString("es-ES");}
  function money(p){return "$"+String(p).replace(".",",");}
  var color={}; D.layers.forEach(function(L,i){color[L.id]="var(--s"+(i%8+1)+")";});

  /* ---- O/S ladder + FD (log y) ---- */
  (function(){
    var host=document.getElementById("ladder"); if(!host||!D.ladder.length) return;
    var lad=D.ladder, fd=D.fd_stack;
    var W=980,H=320,L=64,R=16,T=24,B=40,pw=W-L-R,ph=H-T-B;
    var vals=lad.map(function(d){return d.shares;}); var total=fd.reduce(function(a,b){return a+b.value;},0);
    var lo=Math.floor(Math.log10(Math.min.apply(null,vals))), hi=Math.ceil(Math.log10(Math.max(total,Math.max.apply(null,vals))*1.6));
    function y(v){return T+ph-(Math.log10(v)-lo)/(hi-lo)*ph;}
    var s=el("svg",{viewBox:"0 0 "+W+" "+H,role:"img","aria-label":"O/S histórico en escala logarítmica y dilución total"});
    for(var e=lo;e<=hi;e++){var v=Math.pow(10,e);s.appendChild(el("line",{x1:L,x2:W-R,y1:y(v),y2:y(v),"class":"grid"}));s.appendChild(el("text",{x:L-8,y:y(v)+4,"text-anchor":"end"},fmt(v)));}
    var n=lad.length+1,slot=pw/n,bw=Math.min(56,slot*.62),base=T+ph;
    lad.forEach(function(d,i){var x=L+slot*i+(slot-bw)/2,yy=y(d.shares);
      s.appendChild(tip(el("rect",{x:x,y:yy,width:bw,height:base-yy,rx:3,fill:"var(--bar)"}),d.label+": "+full(d.shares)+" ("+d.src+")"));
      s.appendChild(el("text",{x:x+bw/2,y:yy-6,"text-anchor":"middle","class":"lbl"},fmt(d.shares)));
      s.appendChild(el("text",{x:x+bw/2,y:H-B+16,"text-anchor":"middle"},d.label));});
    var x=L+slot*lad.length+(slot-bw)/2,cum=0;
    fd.forEach(function(d,i){var top=y(cum+d.value),bot=cum?y(cum):base;
      s.appendChild(tip(el("rect",{x:x,y:top,width:bw,height:Math.max(0,bot-top-(cum?2:0)),rx:2,fill:d.id?color[d.id]:"var(--bar)"}),d.name+": "+full(d.value)));cum+=d.value;});
    s.appendChild(el("text",{x:x+bw/2,y:y(cum)-6,"text-anchor":"middle","class":"lbl"},fmt(cum)));
    s.appendChild(el("text",{x:x+bw/2,y:H-B+16,"text-anchor":"middle"},"FD"));
    s.appendChild(el("line",{x1:L,x2:W-R,y1:base,y2:base,"class":"axis"}));
    s.appendChild(el("text",{x:14,y:T+ph/2,transform:"rotate(-90 14 "+(T+ph/2)+")","text-anchor":"middle"},"Acciones, base actual (log)"));
    host.appendChild(s);
    var lg=document.getElementById("ladder-legend");
    if(lg){lg.innerHTML='<span><i style="background:var(--bar)"></i>O/S declarado</span>'+fd.filter(function(d){return d.id;}).map(function(d){return '<span><i style="background:'+color[d.id]+'"></i>'+d.name+'</span>';}).join("");}
  })();

  /* ---- supply by price (log x, stacked) ---- */
  (function(){
    var host=document.getElementById("supply"); if(!host||!D.layers.length) return;
    var ps=D.prices, W=980,H=372,L=64,R=16,T=56,B=44,pw=W-L-R,ph=H-T-B;
    var tops=ps.map(function(_,j){return D.layers.reduce(function(a,Ly){return a+Ly.values[j];},0);});
    var ymax=D.ymax||Math.max.apply(null,tops)*1.1;
    var step=Math.pow(10,Math.floor(Math.log10(ymax/6))); var nice=[1,2,2.5,5,10].map(function(f){return f*step;}).filter(function(s){return ymax/s<=8;})[0]||step*10;
    var xl=Math.log10(D.pmin),xh=Math.log10(D.pmax);
    function X(p){return L+(Math.log10(p)-xl)/(xh-xl)*pw;}
    function Y(v){return T+ph-Math.min(v,ymax)/ymax*ph;}
    var s=el("svg",{viewBox:"0 0 "+W+" "+H,role:"img","aria-label":"Acciones potenciales por nivel de precio, apiladas por capa"});
    for(var v=0;v<=ymax+1;v+=nice){s.appendChild(el("line",{x1:L,x2:W-R,y1:Y(v),y2:Y(v),"class":"grid"}));s.appendChild(el("text",{x:L-8,y:Y(v)+4,"text-anchor":"end"},v?fmt(v):"0"));}
    var below=ps.map(function(){return 0;});
    D.layers.forEach(function(Ly){
      var top=ps.map(function(p,j){return below[j]+Ly.values[j];});
      var d="M"+ps.map(function(p,j){return X(p)+","+Y(top[j]);}).join(" L")+" L"+ps.slice().reverse().map(function(p,k){var j=ps.length-1-k;return X(p)+","+(Y(below[j])-(below[j]?1:0));}).join(" L")+" Z";
      var mid=Math.floor(ps.length/2);
      s.appendChild(tip(el("path",{d:d,fill:color[Ly.id],"fill-opacity":"0.85",stroke:"var(--paper)","stroke-width":"1.5"}),Ly.name+" ("+Ly.gate+")"));
      if(Ly.band_min!=null){var yy=Y(below[0]+Ly.band_min);s.appendChild(el("line",{x1:L,x2:W-R,y1:yy,y2:yy,stroke:"var(--ink)","stroke-dasharray":"5 4","stroke-width":"1.2"}));
        s.appendChild(el("text",{x:L+6,y:yy-5,"class":"lbl"},Ly.name+" mín. "+fmt(Ly.band_min)));}
      below=top;});
    D.marks.forEach(function(m,i){if(m[0]<D.pmin||m[0]>D.pmax)return;var xx=X(m[0]),end=xx>L+pw*.78;
      s.appendChild(el("line",{x1:xx,x2:xx,y1:18+(i%3)*14,y2:T+ph,"class":"mark"}));
      s.appendChild(el("text",{x:end?xx-3:xx+3,y:14+(i%3)*14,"text-anchor":end?"end":"start","class":"lbl"},m[1]));});
    var ticks=[0.1,0.2,0.5,1,2,3,5,10,20,50,100].filter(function(p){return p>=D.pmin&&p<=D.pmax;});
    ticks.forEach(function(p){s.appendChild(el("text",{x:X(p),y:H-B+16,"text-anchor":"middle"},money(p)));});
    s.appendChild(el("line",{x1:L,x2:W-R,y1:T+ph,y2:T+ph,"class":"axis"}));
    s.appendChild(el("text",{x:L+pw/2,y:H-6,"text-anchor":"middle"},"Precio por acción (log)"));
    s.appendChild(el("text",{x:14,y:T+ph/2,transform:"rotate(-90 14 "+(T+ph/2)+")","text-anchor":"middle"},"Acciones nuevas potenciales"));
    host.appendChild(s);
    var lg=document.getElementById("supply-legend");
    if(lg){lg.innerHTML=D.layers.map(function(Ly){return '<span><i style="background:'+color[Ly.id]+'"></i>'+Ly.name+' — '+Ly.gate+'</span>';}).join("");}
  })();
})();
