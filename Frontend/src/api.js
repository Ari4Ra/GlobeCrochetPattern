export const API = "http://127.0.0.1:8000";


export async function generate(params){
const res = await fetch(`${API}/generate`,{
method: "POST",
headers: {"Content-Type":"application/json"},
body: JSON.stringify(params)
});
return await res.json();
}