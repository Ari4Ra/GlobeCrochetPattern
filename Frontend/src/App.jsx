import React, { useState } from 'react'
import { generate } from './api'


export default function App(){
const [params,setParams] = useState({
stitchlength:3,
stitchheight:3,
stitchsetback:0,
diametercm:20,
})


const [markers,setMarkers] = useState([])


async function run(){
const result = await generate(params)
setMarkers(result.markers || [])
}


return (
<div>
<h1>Häkel-Globus Generator</h1>


<div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,maxWidth:400}}>
{Object.keys(params).map(key => (
<label key={key}>
{key}:
<input
type="number"
value={params[key]}
onChange={e=>setParams({...params,[key]:Number(e.target.value)})}
/>
</label>
))}
</div>


<button onClick={run} style={{marginTop:20}}>Generieren</button>


<h2>Ausgabe (erste 50 Marker)</h2>
<pre style={{background:'#eee',padding:10,maxHeight:300,overflow:'auto'}}>
{JSON.stringify(markers.slice(0,50),null,2)}
</pre>
</div>
)
}