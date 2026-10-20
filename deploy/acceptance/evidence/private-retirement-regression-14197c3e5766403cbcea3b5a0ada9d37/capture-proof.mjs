// Read-only snapshot of this uniquely owned synthetic stack before removal.
import {createRequire} from 'node:module';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {writeFileSync,appendFileSync} from 'node:fs';
const require=createRequire(resolve(process.cwd(),'package.json'));
const {Kafka,logLevel}=require('kafkajs'),root=dirname(fileURLToPath(import.meta.url));
if(!root.endsWith('private-retirement-regression-14197c3e5766403cbcea3b5a0ada9d37'))throw Error('EVIDENCE_SCOPE');
const kafka=new Kafka({clientId:'owned-regression-proof',brokers:['127.0.0.1:19092'],logLevel:logLevel.NOTHING}),admin=kafka.admin();
let consumer;
try{
 await admin.connect();const topics=(await admin.listTopics()).filter(t=>t.startsWith('organization.')).sort(),positions=[];
 for(const topic of topics)positions.push({topic,partitions:await admin.fetchTopicOffsets(topic)});
 writeFileSync(join(root,'kafka-boundaries.json'),JSON.stringify(positions,null,2));
 const remaining=new Map(positions.flatMap(t=>t.partitions.filter(p=>BigInt(p.high)>0n).map(p=>[t.topic+':'+p.partition,BigInt(p.high)-1n])));
 writeFileSync(join(root,'kafka-records.jsonl'),'');
 if(remaining.size){
  consumer=kafka.consumer({groupId:'owned-regression-proof-14197c3e5766403cbcea3b5a0ada9d37',allowAutoTopicCreation:false,sessionTimeout:10000});
  await consumer.connect();await consumer.subscribe({topics,fromBeginning:true});let done;const completed=new Promise(resolve=>done=resolve);
  await consumer.run({autoCommit:false,eachMessage:async({topic,partition,message})=>{
   const maximum=positions.find(t=>t.topic===topic)?.partitions.find(p=>p.partition===partition)?.high;
   if(maximum===undefined||BigInt(message.offset)>=BigInt(maximum))return;
   appendFileSync(join(root,'kafka-records.jsonl'),JSON.stringify({topic,partition,offset:message.offset,timestamp:message.timestamp,key_b64:message.key?.toString('base64')??null,value_b64:message.value?.toString('base64')??null,headers:Object.fromEntries(Object.entries(message.headers??{}).map(([k,v])=>[k,Array.isArray(v)?v.map(b=>b.toString('base64')):v.toString('base64')]))})+'\n');
   const key=topic+':'+partition;if(remaining.has(key)&&BigInt(message.offset)>=remaining.get(key))remaining.delete(key);if(!remaining.size)done();
  }});
  let timer;try{await Promise.race([completed,new Promise((_,reject)=>timer=setTimeout(()=>reject(Error('PROOF_RECORD_TIMEOUT')),60000))]);}finally{clearTimeout(timer);}
 }
 async function query(sql){const url=new URL('http://127.0.0.1:18123');url.searchParams.set('query',sql);const response=await fetch(url,{method:'POST',headers:{'X-ClickHouse-User':'acceptance','X-ClickHouse-Key':'synthetic-only-password'},signal:AbortSignal.timeout(15000)});if(!response.ok)throw Error('CLICKHOUSE_PROOF_'+response.status);return response.text();}
 const tables=(await query('SHOW TABLES FROM organization FORMAT JSONEachRow')).trim().split('\n').filter(Boolean).map(JSON.parse).map(t=>t.name).filter(t=>/^[a-z_]+$/.test(t));
 for(const table of tables)writeFileSync(join(root,'clickhouse-'+table+'.jsonl'),await query('SELECT * FROM organization.'+table+' FORMAT JSONEachRow'));
 console.log(JSON.stringify({raw_proof_captured:true,kafka_topics:topics.length,clickhouse_tables:tables.length}));
}finally{await consumer?.disconnect();await admin.disconnect();}
