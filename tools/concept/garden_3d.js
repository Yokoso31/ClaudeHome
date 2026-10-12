/* 3D view of the same garden: lazy-loads three.js on first use, rebuilds the level's pieces on each level change. */
(function(){
  var G=window.__G, SC=G.D.scene, wrap=document.getElementById("v3d"), btn=document.getElementById("v3dbtn"), svg=document.getElementById("plan");
  var cv=document.getElementById("v3dc"), tip=document.getElementById("tip3d"), msg=document.getElementById("v3dmsg");
  var THREE, renderer, scene, camera, controls, groundTex, groundCv, lvGroup, techGroup, ready=false, loading=false, active=false, dirty=true, curL=null;
  var reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
  var MODEC={"Ensoleillé":"#F2C21F","Torride":"#EF5F45","Chaud":"#F59A3C","Frais":"#33B9E2","Glacial":"#7DA8F5"};
  function load(src){ return new Promise(function(res,rej){ var s=document.createElement("script"); s.src=src; s.onload=res; s.onerror=rej; document.head.appendChild(s); }); }
  function on(L,lv){ return lv.indexOf(L)>=0; }
  /* ---------- materials and helpers ---------- */
  var MC={};
  function mat(c,o){ var k=c+JSON.stringify(o||{}); if(!MC[k]){ var p={color:c,roughness:.88,metalness:0,flatShading:true}; for(var i in o) p[i]=o[i]; MC[k]=new THREE.MeshStandardMaterial(p); } return MC[k]; }
  function mesh(g,c,o){ var m=new THREE.Mesh(g,mat(c,o)); m.castShadow=true; m.receiveShadow=true; return m; }
  function box(w,h,d,c,o){ return mesh(new THREE.BoxGeometry(w,h,d),c,o); }
  function cyl(r1,r2,h,c,seg,o){ return mesh(new THREE.CylinderGeometry(r1,r2,h,seg||10),c,o); }
  function ball(r,c,det,o){ return mesh(new THREE.IcosahedronGeometry(r,det==null?1:det),c,o); }
  function cone(r,h,c,seg,o){ return mesh(new THREE.ConeGeometry(r,h,seg||8),c,o); }
  function at(m,x,y,z){ m.position.set(x,y,z); return m; }
  function roof(w,d,h,c){ var m=cone(Math.SQRT1_2,1,c,4); m.rotation.y=Math.PI/4; m.scale.set(w,h,d); m.geometry.computeVertexNormals(); return m; }
  function frame(g,s,h,c){ [[0,-s/2+.06,s,.12],[0,s/2-.06,s,.12],[-s/2+.06,0,.12,s],[s/2-.06,0,.12,s]].forEach(function(e){ g.add(at(box(e[2],h,e[3],c),e[0],h/2,e[1])); }); }
  function grp(o,lab){ var g=new THREE.Group(); g.position.set(o.x+o.w/2-40,0,o.y+o.h/2-30); if(lab) g.userData.lab=lab; return g; }
  var texC={};
  function sprite(key,size,y){ var href=G.iconOf(key); if(!href) return null; if(!texC[key]){ var t=new THREE.TextureLoader().load(href,function(){ dirty=true; }); texC[key]=new THREE.SpriteMaterial({map:t,depthWrite:false}); }
    var s=new THREE.Sprite(texC[key]); s.scale.set(size,size,1); s.position.y=y; s.userData.icon=true; return s; }
  function textSprite(t,size,y,bg,fg){ var c=document.createElement("canvas"); c.width=c.height=128; var x=c.getContext("2d");
    x.fillStyle=bg; x.beginPath(); x.arc(64,64,58,0,7); x.fill(); x.fillStyle=fg; x.font="bold 64px 'IBM Plex Mono',monospace"; x.textAlign="center"; x.textBaseline="middle"; x.fillText(t,64,68);
    var s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),depthWrite:false})); s.scale.set(size,size,1); s.position.y=y; s.userData.icon=true; return s; }
  function rnd(seed){ var s=seed*9301+49297; return function(){ s=(s*9301+49297)%233280; return s/233280; }; }
  /* ---------- trees and plants ---------- */
  function tree(g,h,r,col,seed,extra){ var R=rnd(seed); g.add(at(cyl(r*.14,r*.2,h,"#7A5A3C",7),0,h/2,0));
    for(var i=0;i<5;i++){ var a=i*1.3+R(), d=i?r*.45:0, s=r*(i?.62+R()*.2:.8); g.add(at(ball(s,col),Math.cos(a)*d,h+(i?R()*r*.5-r*.1:r*.25),Math.sin(a)*d)); }
    if(extra) for(var j=0;j<6;j++){ var b=j*1.05; g.add(at(ball(r*.13,extra,0),Math.cos(b)*r*.8,h+r*.1+(j%2)*r*.35,Math.sin(b)*r*.8)); } }
  function palm(g,h,seed){ var R=rnd(seed), t=at(cyl(.12,.18,h,"#8B6B47",6),0,h/2,0); t.rotation.z=.08; g.add(t);
    for(var i=0;i<7;i++){ var l=box(1.7,.06,.42,"#3F8F3A"), a=i*0.9+R()*.3, p=new THREE.Group(); l.position.x=.8; l.rotation.z=-.45; p.add(l); p.rotation.y=a; p.position.y=h; g.add(p); } }
  function bamboo(g,seed){ var R=rnd(seed); for(var i=0;i<6;i++){ var h=3.2+R()*1.6, x=(R()-.5)*1.3, z=(R()-.5)*1.3; g.add(at(cyl(.07,.08,h,"#6FA84A",6),x,h/2,z)); g.add(at(ball(.38,"#5E9A3E",0),x,h,z)); } }
  /* ---------- level pieces ---------- */
  function piece(o,y0){ var g=grp(o,o.lab); g.position.y=y0;
    switch(o.k){
      case "farm": g.add(at(box(1.7,.2,1.7,"#6B4A2E"),0,.1,0)); frame(g,1.9,.3,"#B98A55");
        for(var k=0;k<9;k++){ var px=(k%3-1)*.55, pz=(Math.floor(k/3)-1)*.55; g.add(at(cone(.2,.42,"#4F8A37",5),px,.42,pz)); g.add(at(ball(.13,o.c,0),px,.62,pz)); } break;
      case "wood": g.add(at(box(3.7,.12,3.7,"#7DA453"),0,.06,0)); frame(g,3.85,.28,"#A9794A");
        if(o.t==="palm") palm(g,2.6,o.x*7+o.y);
        else tree(g,1.3,1.25,{citrus:"#4E8F3A",maplet:"#D9662E",cocoa:"#2F6B35",oflower:"#5C9A45"}[o.t]||"#4E8F3A",o.x*7+o.y,{citrus:"#F2D23C",maplet:"#F2A33C",cocoa:"#8A4B2A",oflower:"#FFFFFF"}[o.t]||"#F2D23C");
        break;
      case "shop": var w=o.w, d=o.h, hh=1.5; g.add(at(box(w-.5,hh,d-.5,o.idle?"#D9D5CC":"#E2C9A0"),0,hh/2,0));
        g.add(at(box(w-.3,.12,d-.3,"#5B3F2A"),0,.3,0));
        g.add(at(box(w+.1,.14,d+.1,"#4A3527"),0,hh+.07,0)); g.add(at(roof(w+.1,d+.1,Math.min(w,d)*.42,o.idle?"#8C949C":(o.col||"#3F4D5E")),0,hh+.14+Math.min(w,d)*.21,0));
        var s=sprite(o.ic,Math.min(2.2,Math.max(1.3,w*.45)),hh+Math.min(w,d)*.42+1.2); if(s) g.add(s); break;
      case "pav": g.add(at(box(o.w-.8,1.9,o.h-.8,"#F2D3DE"),0,.95,0)); g.add(at(box(o.w,.14,o.h,"#7C3A55"),0,1.97,0));
        g.add(at(roof(o.w,o.h,1.7,o.col||"#B4587A"),0,2.9,0)); var s2=sprite(o.ic,2,5.1); if(s2) g.add(s2); break;
      case "mine": g.add(at(box(4.8,.12,4.8,"#9C978E"),0,.06,0)); var R=rnd(o.x+o.y);
        [[0,0,1.5],[-1.1,.9,1],[1.2,-.6,.9],[.9,1.2,.7]].forEach(function(p){ var r=ball(p[2],"#8E8A84",0); r.position.set(p[0],p[2]*.7,p[1]); r.rotation.set(R()*3,R()*3,0); g.add(r); });
        g.add(at(ball(.35,"#E7C35A",0,{emissive:"#5A4510"}),.3,2.2,-.2)); var s3=sprite(o.ic,1.8,4); if(s3) g.add(s3); break;
      case "well": g.add(at(cyl(.9,.95,.75,"#A9A39A",12),0,.37,0)); g.add(at(cyl(.62,.62,.78,"#3F86B8",12),0,.4,0));
        g.add(at(box(.12,1.7,.12,"#7A5A3C"),-.75,.85,0)); g.add(at(box(.12,1.7,.12,"#7A5A3C"),.75,.85,0)); g.add(at(roof(1.9,1.3,.6,"#3F5F8F"),0,2,0)); break;
      case "dev":
        if(o.dv==="heat"){ g.add(at(box(.9,.8,.9,"#B5452E"),0,.4,0)); g.add(at(box(.6,.2,.6,"#F59A3C",{emissive:"#C2410C"}),0,.9,0)); }
        else if(o.dv==="cool"){ g.add(at(box(1.8,1.2,1.8,"#BFE3F2"),0,.6,0)); g.add(at(box(1.4,.2,1.4,"#33B9E2",{emissive:"#0E5A75"}),0,1.3,0)); }
        else { g.add(at(cyl(.08,.1,2.2,"#5D6A60",6),0,1.1,0)); g.add(at(ball(.38,"#FFD54A",1,{emissive:"#C99A22"}),0,2.35,0)); }
        g.add(at(cyl(.62,.62,.04,MODEC[o.m]||"#ccc",16,{emissive:MODEC[o.m]||"#000",emissiveIntensity:.25}),0,.02,0)); break;
      case "kiosk": g.add(at(box(1.9,1.3,1.9,"#C99A5B"),0,.65,0)); g.add(at(box(2,.12,2,"#8A6A45"),0,1.36,0)); g.add(textSprite(String(o.n),1.1,2.3,"#203026","#FFFFFF")); break;
      case "gen": g.add(at(cyl(.45,.5,1.3,"#7E63D6",8),0,.65,0)); g.add(at(ball(.3,"#CDBDFB",1,{emissive:"#7E63D6"}),0,1.5,0)); break;
      case "pole": case "bonus": var op=o.k==="bonus"?{transparent:true,opacity:.5}:{};
        g.add(at(box(1.2,.15,1.2,"#B9B2A6",op),0,.07,0)); g.add(at(cyl(.1,.12,3.2,"#5E4B9E",6,op),0,1.6,0)); g.add(at(box(1.1,.08,.08,"#5E4B9E",op),0,2.9,0));
        g.add(at(ball(.17,"#CDBDFB",0,Object.assign({emissive:"#7E63D6"},op)),0,3.25,0));
        if(o.k==="bonus") g.add(textSprite("+"+o.n,1.2,4,"#FFFFFF","#7E63D6")); break;
    }
    return g; }
  /* ---------- decor ---------- */
  function decor(o){ var n=o.n, g=grp(o,n.charAt(0).toUpperCase()+n.slice(1)), s=o.x*13+o.y*7;
    if(n==="Sol en gravier"||n==="Dalle en pierre recouverte de mousse") return null;
    if(n.indexOf("Bambou")===0) bamboo(g,s);
    else if(n==="Bassin"){ g.add(at(cyl(1,1.02,.16,"#6E9E4A",18),0,.08,0)); g.add(at(cyl(.72,.72,.18,"#4C9BC4",18,{roughness:.3}),0,.1,0)); g.add(at(cyl(.18,.18,.02,"#5FA84A",8),-.15,.2,.1)); g.add(at(ball(.16,"#C9C3B8",0),.6,.22,-.6)); }
    else if(n==="Cerisier") tree(g,2.6,2.4,"#F2B8CB",s,"#FFFFFF");
    else if(n.indexOf("Clôture")===0){ g.add(at(box(o.w,.08,o.h,"#C8B48A"),0,.55,0)); var L=Math.max(o.w,o.h), k=Math.round(L/1); for(var i=0;i<=k;i++){ var t=-L/2+i*L/k; g.add(at(box(.12,.8,.12,"#8A6A45"),o.w>o.h?t:0,.4,o.w>o.h?0:t)); } }
    else if(n==="Figurine sculptée en pierre"){ g.add(at(ball(.32,"#A9A39A",0),0,.32,0)); g.add(at(ball(.22,"#A9A39A",0),0,.78,0)); }
    else if(n==="Glycine"){ g.add(at(box(o.w,.08,o.h+.2,"#8A6A45"),0,1.5,0)); for(var j=0;j<4;j++){ var gl=cone(.14,.6,"#9A7BD0",6); gl.rotation.x=Math.PI; g.add(at(gl,-o.w/2+.15+j*(o.w-.3)/3,1.15,0)); } }
    else if(n==="Haie conique") g.add(at(cone(.5,1.7,"#4E8A3E",7),0,.85,0));
    else if(n==="Haie de buis"){ var b=box(o.w,.9,o.h,"#4E8A3E"); g.add(at(b,0,.45,0)); }
    else if(n.indexOf("Lampe en pierre")===0){ var big=o.w>1, sc=big?1:.6; g.add(at(box(.9*sc,.25*sc,.9*sc,"#B9B2A6"),0,.12*sc,0)); g.add(at(box(.3*sc,.8*sc,.3*sc,"#B9B2A6"),0,.62*sc,0));
      g.add(at(box(.7*sc,.5*sc,.7*sc,"#FFE7A0",{emissive:"#E0A93A",emissiveIntensity:.8}),0,1.25*sc,0)); g.add(at(roof(1.2*sc,1.2*sc,.45*sc,"#9E978B"),0,1.72*sc,0)); }
    else if(n==="Mortier en pierre") g.add(at(cyl(.22,.18,.3,"#A9A39A",8),0,.15,0));
    else if(n==="Théière en argile") g.add(at(ball(.22,"#9A5A3C",0),0,.2,0));
    else if(n==="Pin"){ g.add(at(cyl(.22,.3,2.4,"#6E4F35",7),0,1.2,0)); [[0,2.4,1.7],[.6,3.1,1.3],[-.5,3.6,1]].forEach(function(p){ var m=ball(p[2],"#2F5E3A",1); m.scale.y=.45; g.add(at(m,p[0],p[1],p[0]*-.5)); }); }
    else if(n==="Pont en pierre"){ var Lb=Math.max(o.w,o.h), W=Math.min(o.w,o.h)-.4, along=o.h>o.w; for(var q=0;q<9;q++){ var tq=-Lb/2+(q+.5)*Lb/9, hq=.2+Math.sin((q+.5)/9*Math.PI)*.7, seg=box(along?W:Lb/9+.08,.32,along?Lb/9+.08:W,"#B9B2A6"); g.add(at(seg,along?0:tq,hq,along?tq:0)); }
      [-1,1].forEach(function(sd){ for(var q=0;q<9;q++){ var tq=-Lb/2+(q+.5)*Lb/9, hq=.2+Math.sin((q+.5)/9*Math.PI)*.7; g.add(at(box(along?.12:Lb/9+.08,.3,along?Lb/9+.08:.12,"#8F877B"),along?sd*W/2:tq,hq+.3,along?tq:sd*W/2)); } }); }
    else if(n==="Roche - Pics majestueux"){ var R=rnd(s); [[0,0,2.6,7],[-2,1.6,1.8,4.6],[2.2,-1.2,1.6,3.8],[1.4,2.4,1.2,2.6]].forEach(function(p){ var c=cone(p[2],p[3],"#8F8B85",6); c.rotation.y=R()*3; g.add(at(c,p[0],p[3]/2,p[1])); g.add(at(cone(p[2]*.35,p[3]*.18,"#6E9E4A",6),p[0],p[3]*.93,p[1])); }); }
    else if(n==="Roche - Verdure en strates"){ [[3.6,1.2,0],[2.8,1,1.1],[2,.9,2]].forEach(function(p,i){ var m=ball(p[0],i===2?"#6E9E4A":"#8F8B85",0); m.scale.y=p[1]/p[0]*1.2; g.add(at(m,0,p[2]+.5,0)); }); }
    else if(n.indexOf("Souche")===0){ g.add(at(cyl(.4,.45,.5,"#7A5A3C",8),0,.25,0)); g.add(at(cyl(.38,.38,.06,"#6E9E4A",8),0,.52,0)); }
    else if(n==="grand arbre"){ g.userData.lab="Grand arbre violet · taille ×1,6"; g.add(at(cyl(.7,1.1,4,"#6E4F35",8),0,2,0)); var R2=rnd(3);
      for(var a=0;a<11;a++){ var an=a*.57+R2()*.3, dd=a?1.4+R2()*1.6:0, rr=a?1.5+R2()*.9:2.4; g.add(at(ball(rr,["#A98BE0","#C7B2F0","#8C6BD6"][a%3],1),Math.cos(an)*dd,4.6+R2()*1.6,Math.sin(an)*dd)); } }
    else if(n.indexOf("stockage")===0){ g.userData.lab="Stockage "+n.slice(-1); g.add(at(box(1.9,1.3,1.9,"#C99A5B"),0,.65,0)); g.add(at(box(2,.12,2,"#8A6A45"),0,1.36,0)); g.add(textSprite(n.slice(-1),1.1,2.3,"#203026","#FFFFFF")); }
    else if(n==="Érable rouge") tree(g,1.3,1.05,"#D9452B",s);
    else if(n==="éclorateur"){ g.userData.lab="Éclorateur"; g.add(at(cyl(.85,.9,.25,"#5FD3E0",12),0,.12,0)); var e=ball(.72,"#F4F2EC",2); e.scale.y=1.3; g.add(at(e,0,1.1,0)); }
    else if(n==="Arbustes en fleurs"){ g.add(at(ball(.5,"#5E9A3E",1),0,.4,0)); g.add(at(ball(.14,"#F2A7C3",0),.3,.7,.1)); g.add(at(ball(.14,"#F2A7C3",0),-.2,.75,-.2)); }
    else g.add(at(box(o.w,.5,o.h,"#B9B2A6"),0,.25,0));
    return g; }
  /* ---------- ground painted on a texture ---------- */
  var PX=20;
  function paintGround(L){ var c=groundCv.getContext("2d"), W=80*PX, H=60*PX; c.fillStyle="#7EA94E"; c.fillRect(0,0,W,H);
    var R=rnd(7); for(var i=0;i<2600;i++){ c.fillStyle=R()<.5?"rgba(60,110,40,.10)":"rgba(255,255,220,.08)"; c.fillRect(R()*W,R()*H,3+R()*6,3+R()*6); }
    var GC={};   /* only real floor tiles are painted; everything else is the game's own grass */
    SC.ground.forEach(function(z){ if(!on(L,z.lv)||!GC[z.k]) return; c.fillStyle=GC[z.k]; c.fillRect(z.x*PX,z.y*PX,z.w*PX,z.h*PX);
      if(z.k==="z-allee"||z.k==="z-rue"||z.k==="z-eclo"){ c.strokeStyle="rgba(90,80,60,.25)"; c.lineWidth=2; for(var x=z.x;x<=z.x+z.w;x+=1){ c.beginPath(); c.moveTo(x*PX,z.y*PX); c.lineTo(x*PX,(z.y+z.h)*PX); c.stroke(); } for(var y=z.y;y<=z.y+z.h;y+=1){ c.beginPath(); c.moveTo(z.x*PX,y*PX); c.lineTo((z.x+z.w)*PX,y*PX); c.stroke(); } }
      if(z.k==="z-sec"||z.k==="z-nord"){ c.strokeStyle="rgba(150,135,100,.35)"; c.lineWidth=2; for(var y2=z.y+.3;y2<z.y+z.h;y2+=.45){ c.beginPath(); c.moveTo(z.x*PX,y2*PX); c.lineTo((z.x+z.w)*PX,y2*PX); c.stroke(); } }
      if(z.k==="z-cour"){ c.strokeStyle="rgba(150,135,100,.4)"; c.lineWidth=2; for(var r=4.6;r<6;r+=.45){ c.beginPath(); c.arc(40*PX,31*PX,r*PX,0,7); c.stroke(); } }
      if(z.k==="z-fleurs"){ var R3=rnd(5); for(var f=0;f<160;f++){ c.fillStyle=["#F2A7C3","#FFFFFF","#F2D23C","#B79BE8"][f%4]; c.beginPath(); c.arc((z.x+R3()*z.w)*PX,(z.y+R3()*z.h)*PX,4,0,7); c.fill(); } } });
    SC.decor.forEach(function(o){ if(!on(L,o.lv)) return; if(o.n==="Sol en gravier"){ c.fillStyle="#DAD3C4"; c.fillRect(o.x*PX,o.y*PX,o.w*PX,o.h*PX); var R4=rnd(o.x); for(var p=0;p<14;p++){ c.fillStyle="#B9B2A6"; c.beginPath(); c.arc((o.x+R4()*o.w)*PX,(o.y+R4()*o.h)*PX,3+R4()*4,0,7); c.fill(); } }
      if(o.n==="Dalle en pierre recouverte de mousse"){ c.fillStyle="#A3A893"; c.fillRect(o.x*PX+2,o.y*PX+2,o.w*PX-4,o.h*PX-4); }
      if(o.n==="Chaussée en pierre"){ c.fillStyle="#CFCBBA"; c.fillRect(o.x*PX+1,o.y*PX+1,o.w*PX-2,o.h*PX-2); c.strokeStyle="rgba(110,100,80,.35)"; c.lineWidth=2; c.strokeRect(o.x*PX+3,o.y*PX+3,o.w*PX-6,o.h*PX-6); }
      if(o.n==="Chemin de gravier"){ c.fillStyle="#D8CFB8"; c.fillRect(o.x*PX+1,o.y*PX+1,o.w*PX-2,o.h*PX-2); } });
    SC.terr.forEach(function(t){ if(!on(L,t.lv)) return; c.setLineDash([12,8]); c.strokeStyle="rgba(60,90,50,.55)"; c.lineWidth=3; c.strokeRect(t.x*PX,t.y*PX,t.w*PX,t.h*PX); c.setLineDash([]); });
    if(L<16){ c.fillStyle="rgba(40,55,40,.45)"; c.fillRect(40*PX,0,40*PX,15*PX); c.strokeStyle="rgba(255,255,255,.18)"; c.lineWidth=6; for(var h=-15;h<40;h+=2){ c.beginPath(); c.moveTo((40+h)*PX,15*PX); c.lineTo((55+h)*PX,0); c.stroke(); }
      c.fillStyle="rgba(255,255,255,.9)"; c.font="600 "+(PX*1.6)+"px 'IBM Plex Mono',monospace"; c.textAlign="center"; c.fillText("S'ouvre au VR 16",60*PX,8*PX); }
    c.strokeStyle="rgba(255,255,255,.07)"; c.lineWidth=1; for(var gx=0;gx<=80;gx++){ c.beginPath(); c.moveTo(gx*PX,0); c.lineTo(gx*PX,H); c.stroke(); } for(var gy=0;gy<=60;gy++){ c.beginPath(); c.moveTo(0,gy*PX); c.lineTo(W,gy*PX); c.stroke(); }
    groundTex.needsUpdate=true; }
  /* ---------- build a level ---------- */
  var TH=0;
  function inTerr(o,L){ return SC.terr.some(function(t){ return on(L,t.lv) && o.x>=t.x-.01 && o.y>=t.y-.01 && o.x+o.w<=t.x+t.w+.01 && o.y+o.h<=t.y+t.h+.01; }); }
  function build(L){ if(lvGroup){ scene.remove(lvGroup); lvGroup.traverse(function(m){ if(m.geometry) m.geometry.dispose(); }); } if(techGroup) scene.remove(techGroup);
    lvGroup=new THREE.Group(); techGroup=new THREE.Group(); paintGround(L);

    SC.decor.forEach(function(o){ if(!on(L,o.lv)) return; var g=decor(o); if(g) lvGroup.add(g); });
    (SC.levels[L]||[]).forEach(function(o){ lvGroup.add(piece(o,inTerr(o,L)?TH:0));
      if(o.k==="dev"){ var q=new THREE.Mesh(new THREE.PlaneGeometry(9,9),new THREE.MeshBasicMaterial({color:MODEC[o.m]||"#fff",transparent:true,opacity:.22,depthWrite:false})); q.rotation.x=-Math.PI/2; q.position.set(o.x+o.w/2-40,TH+.05,o.y+o.h/2-30); techGroup.add(q); }
      if(o.k==="gen"||o.k==="pole"||o.k==="bonus"){ var s=o.k==="gen"?11:7, p=new THREE.Mesh(new THREE.PlaneGeometry(s,s),new THREE.MeshBasicMaterial({color:"#7E63D6",transparent:true,opacity:o.k==="bonus"?.07:.12,depthWrite:false})); p.rotation.x=-Math.PI/2; p.position.set(o.x+o.w/2-40,.03,o.y+o.h/2-30); techGroup.add(p); } });
    scene.add(lvGroup); techGroup.visible=G.tech(); scene.add(techGroup); showIcons(); curL=L; dirty=true; }
  function showIcons(){ var v=G.names(); if(lvGroup) lvGroup.traverse(function(m){ if(m.userData.icon) m.visible=v; }); dirty=true; }
  /* ---------- camera presets ---------- */
  var VIEWS={all:[[0,52,58],[0,0,4]], gate:[[0,7.5,37],[0,2.5,8]], top:[[0,92,.01],[0,0,0]]};
  /* walk mode: eye height, drag to look around, keys or the on-screen pad to move */
  var walk=false, yaw=0, pitch=-.08, keys={}, pad={}, lastT=0, EYE=2.4;
  function setWalk(on){ walk=on; controls.enabled=!on; document.getElementById("walkpad").hidden=!on; wrap.classList.toggle("walking",on);
    document.querySelectorAll("[data-view]").forEach(function(b){ b.setAttribute("aria-pressed",String(on?b.dataset.view==="walk":false)); });
    if(on){ camera.position.set(0,EYE,29.5); yaw=0; pitch=-.08; look(); } dirty=true; }
  function look(){ var d=new THREE.Vector3(-Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),-Math.cos(yaw)*Math.cos(pitch)); camera.lookAt(camera.position.clone().add(d)); }
  function step(dt){ var f=(keys.f||pad.f?1:0)-(keys.b||pad.b?1:0), s=(keys.r||pad.r?1:0)-(keys.l||pad.l?1:0); if(!f&&!s) return false;
    var sp=(keys.run?11:6)*dt, p=camera.position; p.x+=(-Math.sin(yaw)*f+Math.cos(yaw)*s)*sp; p.z+=(-Math.cos(yaw)*f-Math.sin(yaw)*s)*sp;
    p.x=Math.max(-39.5,Math.min(39.5,p.x)); p.z=Math.max(-29.5,Math.min(29.8,p.z)); p.y=EYE; look(); return true; }
  var KM={ArrowUp:"f",KeyW:"f",KeyZ:"f",ArrowDown:"b",KeyS:"b",ArrowLeft:"l",KeyA:"l",KeyQ:"l",ArrowRight:"r",KeyD:"r",ShiftLeft:"run",ShiftRight:"run"};
  function go(k){ if(k==="walk"){ setWalk(true); return; } if(walk) setWalk(false); var v=VIEWS[k], p0=camera.position.clone(), t0=controls.target.clone(), p1=new THREE.Vector3().fromArray(v[0]), t1=new THREE.Vector3().fromArray(v[1]);
    if(reduce){ camera.position.copy(p1); controls.target.copy(t1); controls.update(); dirty=true; return; }
    var st=performance.now(); (function step(){ var a=Math.min(1,(performance.now()-st)/700), e=a<.5?2*a*a:1-Math.pow(-2*a+2,2)/2; camera.position.lerpVectors(p0,p1,e); controls.target.lerpVectors(t0,t1,e); controls.update(); dirty=true; if(a<1) requestAnimationFrame(step); })(); }
  /* ---------- init ---------- */
  function size(){ var w=wrap.clientWidth, h=Math.round(w*(matchMedia("(max-width:640px)").matches?1:.72)); renderer.setSize(w,h,false); cv.style.height=h+"px"; camera.aspect=w/h; camera.updateProjectionMatrix(); dirty=true; }
  function init(){ THREE=window.THREE; renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true}); renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1)); renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
    scene=new THREE.Scene(); scene.background=new THREE.Color("#CFE3EC"); scene.fog=new THREE.Fog("#CFE3EC",110,190);
    camera=new THREE.PerspectiveCamera(45,1.4,.5,400); camera.position.fromArray(VIEWS.all[0]);
    scene.add(new THREE.HemisphereLight("#E8F1FA","#4E6236",.5));
    var sun=new THREE.DirectionalLight("#FFEBC8",.62); sun.position.set(-35,60,28); sun.castShadow=true; sun.shadow.mapSize.set(2048,2048);
    var sc=sun.shadow.camera; sc.left=-52; sc.right=52; sc.top=42; sc.bottom=-42; sc.near=10; sc.far=160; sun.shadow.bias=-.0006; scene.add(sun);
    var far=new THREE.Mesh(new THREE.PlaneGeometry(400,400),new THREE.MeshStandardMaterial({color:"#6E9449",roughness:1})); far.rotation.x=-Math.PI/2; far.position.y=-.05; far.receiveShadow=true; scene.add(far);
    groundCv=document.createElement("canvas"); groundCv.width=80*PX; groundCv.height=60*PX; groundTex=new THREE.CanvasTexture(groundCv); groundTex.anisotropy=4;
    var gr=new THREE.Mesh(new THREE.PlaneGeometry(80,60),new THREE.MeshStandardMaterial({map:groundTex,roughness:1})); gr.rotation.x=-Math.PI/2; gr.receiveShadow=true; scene.add(gr);
    [[0,-30.25,80.8,.5],[0,30.25,80.8,.5],[-40.25,0,.5,60],[40.25,0,.5,60]].forEach(function(e){ var b=new THREE.Mesh(new THREE.BoxGeometry(e[2],.4,e[3]),mat("#9E978B")); b.position.set(e[0],.2,e[1]); b.receiveShadow=true; scene.add(b); });
    controls=new THREE.OrbitControls(camera,cv); controls.target.fromArray(VIEWS.all[1]); controls.enableDamping=!reduce; controls.dampingFactor=.08; controls.maxPolarAngle=Math.PI*.47; controls.minDistance=6; controls.maxDistance=140; controls.screenSpacePanning=false;
    controls.addEventListener("change",function(){ dirty=true; tip.hidden=true; }); controls.update();
    var ray=new THREE.Raycaster(), mv=new THREE.Vector2();
    function pick(ev){ var r=cv.getBoundingClientRect(); mv.set((ev.clientX-r.left)/r.width*2-1,-(ev.clientY-r.top)/r.height*2+1); ray.setFromCamera(mv,camera);
      var hit=ray.intersectObjects(lvGroup.children,true)[0], lab=null;
      if(hit){ var o=hit.object; while(o && !o.userData.lab) o=o.parent; lab=o&&o.userData.lab; }
      if(!lab){ tip.hidden=true; return; } tip.textContent=lab; tip.hidden=false; var pr=wrap.getBoundingClientRect();
      tip.style.left=Math.min(ev.clientX-pr.left+12,pr.width-tip.offsetWidth-6)+"px"; tip.style.top=Math.max(4,ev.clientY-pr.top-tip.offsetHeight-12)+"px"; }
    var drag=null;
    var moved=0;
    cv.addEventListener("pointerdown",function(ev){ moved=0; if(walk){ drag={x:ev.clientX,y:ev.clientY}; cv.setPointerCapture(ev.pointerId); } });
    cv.addEventListener("pointerup",function(){ drag=null; });
    cv.addEventListener("pointermove",function(ev){ if(walk&&drag){ moved+=Math.abs(ev.clientX-drag.x)+Math.abs(ev.clientY-drag.y); yaw+=(ev.clientX-drag.x)*.005; pitch=Math.max(-1.2,Math.min(1.1,pitch-(ev.clientY-drag.y)*.004)); drag={x:ev.clientX,y:ev.clientY}; look(); dirty=true; tip.hidden=true; return; }
      if(ev.pointerType==="mouse"&&!ev.buttons) pick(ev); });
    cv.tabIndex=0;
    cv.addEventListener("keydown",function(ev){ var k=KM[ev.code]; if(walk&&k){ keys[k]=true; ev.preventDefault(); } });
    cv.addEventListener("keyup",function(ev){ var k=KM[ev.code]; if(k) keys[k]=false; });
    cv.addEventListener("blur",function(){ keys={}; });
    document.querySelectorAll("#walkpad [data-mv]").forEach(function(b){ var k=b.dataset.mv;
      b.addEventListener("pointerdown",function(e){ pad[k]=true; b.setPointerCapture(e.pointerId); e.preventDefault(); });
      ["pointerup","pointercancel","pointerleave"].forEach(function(t){ b.addEventListener(t,function(){ pad[k]=false; }); }); });
    cv.addEventListener("click",function(ev){ if(moved>6) return; pick(ev); }); cv.addEventListener("pointerleave",function(){ tip.hidden=true; });
    document.querySelectorAll("[data-view]").forEach(function(b){ b.addEventListener("click",function(){ go(b.dataset.view); }); });
    window.addEventListener("resize",function(){ if(active) size(); });
    size(); ready=true; build(G.level()); msg.hidden=true;
    (function loop(t){ requestAnimationFrame(loop); var dt=Math.min(.05,((t||0)-lastT)/1000); lastT=t||0; if(!active) return;
      if(walk){ if(step(dt)) dirty=true; } else if(controls.enableDamping && controls.update()) dirty=true;
      if(dirty){ renderer.render(scene,camera); dirty=false; } })(); }
  function show(on){ active=on; btn.setAttribute("aria-pressed",String(on)); wrap.hidden=!on; svg.style.display=on?"none":""; document.getElementById("tipc").hidden=true;
    if(on && !ready && !loading){ loading=true; msg.hidden=false; msg.textContent="Chargement de la 3D…";
      load("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js").then(function(){ return load("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"); }).then(init)
        .catch(function(){ loading=false; msg.textContent="La 3D n'a pas pu se charger (connexion ou navigateur). Le plan 2D reste disponible."; }); }
    if(on && ready){ size(); if(curL!==G.level()) build(G.level()); } }
  btn.addEventListener("click",function(){ show(!active); });
  window.G3D={level:function(L){ if(ready) build(L); }, names:function(){ if(ready) showIcons(); }, tech:function(v){ if(ready){ techGroup.visible=v; dirty=true; } }};
})();
