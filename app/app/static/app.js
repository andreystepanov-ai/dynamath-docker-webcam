(() => {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  const el = id => document.getElementById(id);

  const speed = el('ctrl-speed');
  const pull  = el('ctrl-pull');
  const thr   = el('ctrl-thr');
  const a     = el('ctrl-a');
  const b     = el('ctrl-b');
  const g     = el('ctrl-g');
  const btnF  = el('btn-freeze');
  const btnR  = el('btn-reset');
  const btnW  = el('btn-webcam');

  const setVal = (inp, spanId) => el(spanId).textContent = Number(inp.value).toFixed(3);
  ['speed','pull','thr','a','b','g'].forEach(k => setVal(el('ctrl-'+k), 'val-'+k));

  let frozen = false;
  btnF.onclick = () => { frozen = !frozen; btnF.textContent = frozen ? 'Unfreeze' : 'Freeze flow'; sendControls(); };
  btnR.onclick = () => { ws.readyState===1 && ws.send(JSON.stringify({type:'reset'})); };
  ;[speed,pull,thr,a,b,g].forEach(inp => inp.addEventListener('input', () => { setVal(inp,'val-'+inp.id.split('ctrl-')[1]); sendControls(); }));

  function sendControls(){
    if (ws.readyState !== 1) return;
    ws.send(JSON.stringify({
      type:'control',
      payload:{
        speed_dt: frozen ? 0.0 : Number(speed.value),
        pull_k: Number(pull.value),
        edge_threshold: Number(thr.value),
        alpha: Number(a.value),
        beta: Number(b.value),
        gamma: Number(g.value)
      }
    }));
  }

  // Webcam → sensor
  const cam = el('cam');
  const camc = el('camc');
  const cctx = camc.getContext('2d', { willReadFrequently:true });
  let prevFrame = null, webcamEnabled=false, lastSensorSent=0;

  btnW.onclick = async () => {
    if (webcamEnabled){ webcamEnabled=false; btnW.textContent='Enable webcam'; return; }
    try{
      const stream = await navigator.mediaDevices.getUserMedia({video:{width:320,height:240}, audio:false});
      cam.srcObject = stream; webcamEnabled=true; btnW.textContent='Disable webcam'; loopCam();
    }catch(e){ console.error(e); alert('Camera access denied or not available.'); }
  };

  function loopCam(){
    if (!webcamEnabled) return;
    cctx.drawImage(cam,0,0,camc.width,camc.height);
    const img = cctx.getImageData(0,0,camc.width,camc.height);
    const data = img.data;

    let sumY=0,sumR=0,sumG=0,sumB=0,motion=0;
    for (let i=0;i<data.length;i+=4){
      const r=data[i], g=data[i+1], b=data[i+2];
      const y = 0.299*r + 0.587*g + 0.114*b; sumY+=y; sumR+=r; sumG+=g; sumB+=b;
      if (prevFrame){ motion += Math.abs(y - prevFrame[i/4]) / 255; }
    }
    const pixels = (data.length/4)||1;
    const meanY = (sumY/pixels)/255;
    const meanR = (sumR/pixels)/255, meanG=(sumG/pixels)/255, meanB=(sumB/pixels)/255;
    const hueProxy = Math.atan2(meanG-meanB, meanR-meanG);
    const mot = Math.min(1, motion/pixels*3.0);
    if (!prevFrame) prevFrame = new Float32Array(pixels);
    let j=0; for (let i=0;i<data.length;i+=4){ const r=data[i],g=data[i+1],b=data[i+2]; prevFrame[j++]=0.299*r+0.587*g+0.114*b; }

    const now = performance.now();
    if (ws.readyState===1 && now-lastSensorSent>100){
      lastSensorSent=now;
      ws.send(JSON.stringify({type:'sensor', payload:{motion:mot, brightness:meanY, hue:hueProxy, rgb:[meanR,meanG,meanB]}}));
    }
    requestAnimationFrame(loopCam);
  }

  // Viz + autofit + heartbeat
  const scene = el('scene'), sctx = scene.getContext('2d');
  const chart = el('chart'), mctx = chart.getContext('2d');

  const series = { drift: [], entropy: [] };
  function drawChart(d,e){
    series.drift.push(d); series.entropy.push(e);
    if (series.drift.length>400){ series.drift.shift(); series.entropy.shift(); }
    mctx.clearRect(0,0,chart.width,chart.height);
    const pad=20, w=chart.width-2*pad, h=chart.height-2*pad;
    mctx.strokeStyle='#1f2a44'; mctx.strokeRect(pad,pad,w,h);
    const maxD=Math.max(1,...series.drift), maxE=Math.max(1,...series.entropy);
    const plot=(arr,color,maxv)=>{ mctx.beginPath(); mctx.strokeStyle=color;
      arr.forEach((v,i)=>{ const x=pad+i*(w/Math.max(1,arr.length-1)); const y=pad+h - (h*(v/(maxv||1)));
        if(i===0) mctx.moveTo(x,y); else mctx.lineTo(x,y); }); mctx.stroke(); };
    plot(series.drift,'#60a5fa',maxD); plot(series.entropy,'#f97316',maxE);
  }

  // smooth-fitting state
  const fit = { minX:0, minY:0, maxX:1, maxY:1, s:1, ox:0, oy:0, init:false };
  const EMA = 0.15;               // сглаживание bbox
  const PADDING = 0.10;           // поля 10%
  const S_MIN = 0.4, S_MAX = 6.0; // пределы зума относительно «номинального»

  let heartbeatPhase = 0, heartbeatAmp = 0.0; // визуальный пульс

  function updateFit(emb){
    let minX=+Infinity,minY=+Infinity,maxX=-Infinity,maxY=-Infinity;
    for(const [x,y] of emb){ if(x<minX)minX=x; if(x>maxX)maxX=x; if(y<minY)minY=y; if(y>maxY)maxY=y; }
    if (!isFinite(minX) || maxX===minX || maxY===minY){ minX=0;maxX=1;minY=0;maxY=1; }

    if (!fit.init){ fit.minX=minX;fit.maxX=maxX;fit.minY=minY;fit.maxY=maxY; fit.init=true; }
    else{
      fit.minX = fit.minX*(1-EMA) + minX*EMA;
      fit.maxX = fit.maxX*(1-EMA) + maxX*EMA;
      fit.minY = fit.minY*(1-EMA) + minY*EMA;
      fit.maxY = fit.maxY*(1-EMA) + maxY*EMA;
    }

    const dx = (fit.maxX-fit.minX)||1, dy=(fit.maxY-fit.minY)||1;
    const sx = (1-2*PADDING)*scene.width / dx;
    const sy = (1-2*PADDING)*scene.height/ dy;
    let s = Math.min(sx,sy);
    // нормализуем относительно первого кадра
    if (!isFinite(fit.s) || fit.s===0) fit.s = s;
    else fit.s = fit.s*(1-EMA) + s*EMA;
    fit.s = Math.max(S_MIN* (scene.width/920), Math.min(S_MAX*(scene.width/920), fit.s));

    const ox = PADDING*scene.width - fit.s*fit.minX;
    const oy = PADDING*scene.height - fit.s*fit.minY;
    fit.ox = fit.ox*(1-EMA) + ox*EMA;
    fit.oy = fit.oy*(1-EMA) + oy*EMA;

    return ([x,y]) => [fit.ox + fit.s*x, fit.oy + fit.s*y];
  }

  ws.onopen = () => sendControls();
  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    const { emb, edges, drift, entropy } = data;

    // heartbeat: частота растёт с дрейфом, амплитуда — с нормализованной активностью
    const freq = 1.0 + Math.min(3.0, drift*0.2);           // 1..~4 Гц
    const ampTarget = Math.min(1.0, 0.15 + 0.12*drift);     // 0.15..1
    heartbeatAmp = heartbeatAmp*0.9 + ampTarget*0.1;
    heartbeatPhase += (2*Math.PI) * freq * (1/60);          // ~60fps-счётчик

    const W=scene.width, H=scene.height;
    sctx.clearRect(0,0,W,H);
    const grd=sctx.createLinearGradient(0,0,0,H);
    grd.addColorStop(0,'#0f1734'); grd.addColorStop(1,'#0b1228');
    sctx.fillStyle=grd; sctx.fillRect(0,0,W,H);

    const toPx = updateFit(emb);

    // edges
    sctx.lineCap='round';
    edges.forEach(([i,j,w])=>{
      const p1 = toPx(emb[i]), p2 = toPx(emb[j]);
      const width = Math.min(18, Math.max(1, (w/3.2e7)*10));
      sctx.strokeStyle='#2dd4bf'; sctx.lineWidth=width;
      sctx.beginPath(); sctx.moveTo(p1[0],p1[1]); sctx.lineTo(p2[0],p2[1]); sctx.stroke();
    });

    // nodes + heartbeat
    const pulse = 1 + heartbeatAmp * Math.sin(heartbeatPhase);
    emb.forEach(p=>{
      const [px,py]=toPx(p);
      const r = 6*pulse, r2 = 12*pulse;
      sctx.fillStyle='rgba(255,221,87,0.92)';
      sctx.beginPath(); sctx.arc(px,py,r,0,Math.PI*2); sctx.fill();
      sctx.fillStyle='rgba(255,221,87,0.32)';
      sctx.beginPath(); sctx.arc(px,py,r2,0,Math.PI*2); sctx.fill();
    });

    drawChart(drift,entropy);
  };

  ws.onclose = () => setTimeout(()=>location.reload(),1500);
})();
