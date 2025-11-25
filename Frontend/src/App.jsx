import React, { useState, useEffect } from 'react'
import { generate, API } from './api'


export default function App(){
const [params,setParams] = useState({
stitchlength:2,
stitchheight:2,
stitchsetback:1,
diametercm:1,
})


const [markers,setMarkers] = useState([])
const [index, setIndex] = useState(0)
const [stats, setStats] = useState(null);


//async function run(){
//const result = await generate(params)
//setMarkers(result)
//}

function formatMarker(marker) {
  return marker.map(entry => {
    const [count, _mal, inc, c1, c2] = entry;

    // Normale Masche
    if (inc === 0) {
      return `${count} × sc ${c1}`;
    }

    // Zunahme / Doppelmasche
    if (inc === 1) {
      if (!c2 || c2 === c1) {
        return `${count} × dc ${c1}`;
      } else {
        return `${count} × dc (${c1} + ${c2})`;
      }
    }

    // Abnahme – nur eine Farbe
    if (inc === -1) {
      return `${count} × dec ${c1}`;
    }

    // Für unbekannte Fälle
    return `${count} × ??? (${c1}${c2 ? " + " + c2 : ""})`;
  });
}

useEffect(() => {
  function handleKeyDown(e) {
    if (e.key === "ArrowRight") {
      setIndex(i => Math.min(i + 1, markers.length - 1));
    }
    if (e.key === "ArrowLeft") {
      setIndex(i => Math.max(i - 1, 0));
    }
  }

  window.addEventListener("keydown", handleKeyDown);
  return () => window.removeEventListener("keydown", handleKeyDown);
}, [markers]);



async function run() {
    //console.log("Full fetch URL:", `${API}/generate`);
    //console.log("Params:", params);
    const result = await generate(params);
    //console.log("Result from backend:", result);
    setMarkers(result.pattern);
    setIndex(0)
    setStats(result.statistics);
}

const current = markers[index]   // das aktuell ausgewählte Element

  function prev(){
    setIndex(i => Math.max(0, i - 1))
  }

  function next(){
    setIndex(i => Math.min(markers.length - 1, i + 1))
  }


return (
    <div>
      <h1>Häkel-Globus Generator</h1>

      <div style={{
        display:'grid',
        gridTemplateColumns:'1fr 1fr',
        gap:10,
        maxWidth:400
      }}>
        {Object.keys(params).map(key => (
          <label key={key}>
            {key}:
            <input
              type="number"
              type="number"
              min="0"
              step="0.1"
              value={params[key]}
              onChange={e=>setParams({...params,[key]:Number(e.target.value)})}
            />
          </label>
        ))}
      </div>



      <button onClick={run} style={{marginTop:20}}>
        Generieren
      </button>

      <h2>Ausgabe</h2>

      {markers.length === 0 ? (
        <p>Keine Daten.</p>
      ) : (
        <div>
          <div style={{display:"flex", alignItems:"center", gap:10}}>

            {/* ← Pfeil */}
            <button onClick={prev} disabled={index === 0}>
              ←
            </button>

            {/* Anzeige des aktuellen Elements */}
              <pre style={{
                background:'#eee',
                padding:10,
                maxHeight:300,
                overflow:'auto',
                flexGrow:1,
                whiteSpace: 'pre-wrap'
            }}>
                {formatMarker(current).map((line, i) => (
                    <div key={i}>{line}</div>
                ))}
            </pre>


            {/* → Pfeil */}
            <button onClick={next} disabled={index === markers.length - 1}>
              →
            </button>
          </div>

          <p style={{marginTop:10}}>
            Element {index + 1} von {markers.length}
          </p>
        </div>
      )}
{/* Statistik – oben rechts */}
<div style={{
  position: "absolute",
  top: 20,
  right: 200,
  background: "white",
  padding: "10px 15px",
  border: "1px solid #ccc",
  borderRadius: 8,
  maxWidth: 400
}}>
  <h3>Statistik</h3>

  <table style={{ width: "100%", borderCollapse: "collapse" }}>
    <thead>
      <tr>
        <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Farbe</th>
        <th style={{ textAlign: "right", borderBottom: "1px solid #ccc" }}>Anzahl</th>
      </tr>
    </thead>
    <tbody>
      {Object.entries(stats || {}).map(([color, count]) => (
        <tr key={color}>
          <td>{color}</td>
          <td style={{ textAlign: "right" }}>{count}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>


    </div>
  )
}


