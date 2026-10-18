(function(){
var D=JSON.parse(document.getElementById("chart-data").textContent);
var NS="http://www.w3.org/2000/svg";
function el(t,a,txt){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e;}
function tip(e,s){e.appendChild(el("title",{},s));return e;}
function n1(v){return (Math.round(v*10)/10).toFixed(1).replace(".",",").replace("-","−");}
function svg(w,h,label){return el("svg",{viewBox:"0 0 "+w+" "+h,role:"img","aria-label":label});}

/* 1 · revenue growth YoY (bars) + acceleration (pp, lower strip) */
(function(){
  var host=document.getElementById("growth"); if(!host||!D.series.length)return;
  var S=D.series.slice(-8), W=760, L=48, R=16, T=24, H1=190, gap=34, H2=80, B=26, H=T+H1+gap+H2+B;
  var s=svg(W,H,"Crecimiento interanual de ingresos y aceleración por trimestre");
  var cw=(W-L-R)/S.length, bw=Math.min(46,cw*0.56);
  var ymax=Math.max.apply(null,S.map(function(d){return d.yoy*100;}).concat([10]));
  var ymin=Math.min.apply(null,S.map(function(d){return d.yoy*100;}).concat([0]));
  ymax=Math.ceil(ymax/10)*10; ymin=Math.floor(ymin/10)*10;
  function y1(v){return T+H1-(v-ymin)/(ymax-ymin)*H1;}
  for(var g=ymin;g<=ymax;g+=10){s.appendChild(el("line",{x1:L,x2:W-R,y1:y1(g),y2:y1(g),"class":"grid"}));
    s.appendChild(el("text",{x:L-6,y:y1(g)+4,"text-anchor":"end"},g+"%"));}
  s.appendChild(el("text",{x:L,y:12,"class":"lbl"},"Ingresos, crecimiento interanual"));
  var accs=S.map(function(d){return d.accel==null?0:Math.abs(d.accel);}); var amax=Math.max.apply(null,accs.concat([5]));
  var top2=T+H1+gap, mid2=top2+H2/2;
  function y2(v){return mid2-v/amax*(H2/2-4);}
  s.appendChild(el("text",{x:L,y:top2-10,"class":"lbl"},"Aceleración (pp frente al trimestre anterior)"));
  s.appendChild(el("line",{x1:L,x2:W-R,y1:mid2,y2:mid2,"class":"axis"}));
  S.forEach(function(d,i){
    var cx=L+cw*i+cw/2, v=d.yoy*100, y=y1(Math.max(v,0)), h=Math.abs(y1(v)-y1(0));
    var last=i===S.length-1;
    tip(s.appendChild(el("rect",{x:cx-bw/2,y:v>=0?y:y1(0),width:bw,height:Math.max(h,1),rx:2,style:"fill:var("+(last?"--accent":"--dot")+")"})),d.period+": "+n1(v)+"% interanual");
    s.appendChild(el("text",{x:cx,y:(v>=0?y:y1(v))-5+(v>=0?0:16),"text-anchor":"middle","class":last?"lbl":""},n1(v)+"%"));
    s.appendChild(el("text",{x:cx,y:H-8,"text-anchor":"middle"},d.period));
    if(d.accel!=null){var a=d.accel, ya=y2(Math.max(a,0)), ha=Math.abs(y2(a)-mid2);
      tip(s.appendChild(el("rect",{x:cx-bw/2,y:a>=0?ya:mid2,width:bw,height:Math.max(ha,1),rx:2,style:"fill:var("+(a>=0?"--up":"--down")+")"})),d.period+": "+(a>=0?"+":"")+n1(a)+" pp");
      s.appendChild(el("text",{x:cx,y:a>=0?ya-4:mid2+ha+12,"text-anchor":"middle"},(a>=0?"+":"")+n1(a)));}
  });
  host.appendChild(s);
})();

/* 2 · peer quadrant: growth (x) vs EV/sales (y), medians split the plane */
(function(){
  var host=document.getElementById("quadrant"); if(!host||D.peers.length<2)return;
  var P=D.peers, W=760, H=380, L=56, R=20, T=22, B=40;
  var s=svg(W,H,"Pares: crecimiento interanual frente a EV/ventas");
  var xs=P.map(function(p){return p.x*100;}), ys=P.map(function(p){return p.y;});
  var x0=Math.min(0,Math.floor(Math.min.apply(null,xs)/10)*10), x1=Math.ceil(Math.max.apply(null,xs)/10)*10+5;
  var y0=0, y1=Math.ceil(Math.max.apply(null,ys)*1.12/2)*2;
  function X(v){return L+(v-x0)/(x1-x0)*(W-L-R);} function Y(v){return T+(1-(v-y0)/(y1-y0))*(H-T-B);}
  for(var g=x0;g<=x1;g+=10){s.appendChild(el("line",{x1:X(g),x2:X(g),y1:T,y2:H-B,"class":"grid"}));s.appendChild(el("text",{x:X(g),y:H-B+16,"text-anchor":"middle"},g+"%"));}
  for(var h=0;h<=y1;h+=2){s.appendChild(el("line",{x1:L,x2:W-R,y1:Y(h),y2:Y(h),"class":"grid"}));s.appendChild(el("text",{x:L-6,y:Y(h)+4,"text-anchor":"end"},h+"×"));}
  function med(a){a=a.slice().sort(function(p,q){return p-q;});var m=a.length>>1;return a.length%2?a[m]:(a[m-1]+a[m])/2;}
  var mx=med(xs), my=med(ys);
  s.appendChild(el("line",{x1:X(mx),x2:X(mx),y1:T,y2:H-B,"class":"med"}));
  s.appendChild(el("line",{x1:L,x2:W-R,y1:Y(my),y2:Y(my),"class":"med"}));
  s.appendChild(el("text",{x:W-R-4,y:H-B-8,"text-anchor":"end","class":"q"},"MÁS CRECIMIENTO · MÚLTIPLO MENOR"));
  s.appendChild(el("text",{x:W-R-4,y:T+12,"text-anchor":"end","class":"q"},"MÁS CRECIMIENTO · MÚLTIPLO MAYOR"));
  s.appendChild(el("text",{x:L+6,y:T+12,"class":"q"},"MENOS CRECIMIENTO · MÚLTIPLO MAYOR"));
  s.appendChild(el("text",{x:L+6,y:H-B-8,"class":"q"},"MENOS CRECIMIENTO · MÚLTIPLO MENOR"));
  s.appendChild(el("text",{x:(L+W-R)/2,y:H-6,"text-anchor":"middle"},"Crecimiento interanual de ingresos"));
  P.forEach(function(p){
    var cx=X(p.x*100), cy=Y(p.y);
    tip(s.appendChild(el("circle",{cx:cx,cy:cy,r:p.s?8:5.5,style:"fill:var("+(p.s?"--accent":"--dot")+");stroke:var(--paper);stroke-width:2"})),p.t+": "+n1(p.x*100)+"% · "+n1(p.y)+"×");
    s.appendChild(el("text",{x:cx+(p.s?12:9),y:cy+4,"class":p.s?"lbl":""},p.t));
  });
  host.appendChild(s);
})();
})();
