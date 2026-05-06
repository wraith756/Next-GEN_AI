import { useState, useEffect } from 'react'

interface SysCmd { id: number; name: string; path: string }
interface WebCmd { id: number; name: string; url: string }
interface Contact { id: number; name: string; mobile_no: string; email: string; address: string }
interface Info { name: string; designation: string; mobileno: string; email: string; city: string }

export default function SettingsModal() {
  const [info, setInfo] = useState<Info>({ name: '', designation: '', mobileno: '', email: '', city: '' })
  const [sysCmds, setSysCmds] = useState<SysCmd[]>([])
  const [webCmds, setWebCmds] = useState<WebCmd[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])

  useEffect(() => {
    fetch('/api/settings/info').then(r => r.json()).then(d => d && setInfo(d))
    fetch('/api/settings/syscommands').then(r => r.json()).then(setSysCmds)
    fetch('/api/settings/webcommands').then(r => r.json()).then(setWebCmds)
    fetch('/api/settings/contacts').then(r => r.json()).then(setContacts)
  }, [])

  async function saveInfo() {
    await fetch('/api/settings/info', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(info) })
    alert('Updated Successfully')
  }

  async function addSysCmd(name: string, path: string) {
    await fetch('/api/settings/syscommands', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, path }) })
    fetch('/api/settings/syscommands').then(r => r.json()).then(setSysCmds)
  }

  async function deleteSysCmd(id: number) {
    await fetch(`/api/settings/syscommands/${id}`, { method: 'DELETE' })
    setSysCmds(prev => prev.filter(c => c.id !== id))
  }

  async function addWebCmd(name: string, url: string) {
    await fetch('/api/settings/webcommands', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, url }) })
    fetch('/api/settings/webcommands').then(r => r.json()).then(setWebCmds)
  }

  async function deleteWebCmd(id: number) {
    await fetch(`/api/settings/webcommands/${id}`, { method: 'DELETE' })
    setWebCmds(prev => prev.filter(c => c.id !== id))
  }

  async function addContact(name: string, mobile_no: string, email: string, address: string) {
    await fetch('/api/settings/contacts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, mobile_no, email, address }) })
    fetch('/api/settings/contacts').then(r => r.json()).then(setContacts)
  }

  async function deleteContact(id: number) {
    await fetch(`/api/settings/contacts/${id}`, { method: 'DELETE' })
    setContacts(prev => prev.filter(c => c.id !== id))
  }

  return (
    <div className="modal fade" id="settingsModal" tabIndex={-1} aria-hidden="true">
      <div className="modal-dialog modal-xl">
        <div className="modal-content glass-effect">
          <div className="modal-header">
            <h5 className="modal-title" style={{ color: 'white' }}>Assistant Settings</h5>
            <button type="button" className="btn-close btn-glow-red" data-bs-dismiss="modal" aria-label="Close" />
          </div>
          <div className="modal-body">
            <nav>
              <div className="nav nav-tabs" role="tablist">
                <button className="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-personal" type="button">Personal</button>
                <button className="nav-link" data-bs-toggle="tab" data-bs-target="#tab-commands" type="button">Commands</button>
                <button className="nav-link" data-bs-toggle="tab" data-bs-target="#tab-contacts" type="button">Phone Book</button>
              </div>
            </nav>
            <div className="tab-content mt-3">

              <div className="tab-pane fade show active" id="tab-personal">
                <div className="p-4">
                  {(['name', 'designation', 'mobileno', 'email', 'city'] as const).map(f => (
                    <div className="mb-3" key={f}>
                      <input type="text" className="form-control glassy-form" placeholder={f}
                        value={info[f]} onChange={e => setInfo(p => ({ ...p, [f]: e.target.value }))} />
                    </div>
                  ))}
                  <div className="text-center mt-4">
                    <button className="btn btn-glow" onClick={saveInfo}>Save</button>
                  </div>
                </div>
              </div>

              <div className="tab-pane fade" id="tab-commands">
                <SysCmdSection cmds={sysCmds} onAdd={addSysCmd} onDelete={deleteSysCmd} />
                <WebCmdSection cmds={webCmds} onAdd={addWebCmd} onDelete={deleteWebCmd} />
              </div>

              <div className="tab-pane fade" id="tab-contacts">
                <ContactSection contacts={contacts} onAdd={addContact} onDelete={deleteContact} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SysCmdSection({ cmds, onAdd, onDelete }: { cmds: SysCmd[]; onAdd: (n: string, p: string) => void; onDelete: (id: number) => void }) {
  const [name, setName] = useState(''); const [path, setPath] = useState('')
  return (
    <div className="p-2">
      <p className="text-white">System Commands</p>
      <div className="d-flex mt-2 gap-2">
        <input className="form-control glassy-form" placeholder="keyword eg: notepad" value={name} onChange={e => setName(e.target.value)} />
        <input className="form-control glassy-form" placeholder="path eg: c:/notepad.exe" value={path} onChange={e => setPath(e.target.value)} />
        <button className="btn btn-glow" style={{ width: 'auto', whiteSpace: 'nowrap' }} onClick={() => { if (name && path) { onAdd(name, path); setName(''); setPath('') } }}>Add</button>
      </div>
      <div className="table-responsive table-scroll mt-3">
        <table className="table"><thead><tr><th className="text-light">#</th><th className="text-light">Keyword</th><th className="text-light">Path</th><th className="text-light">Delete</th></tr></thead>
          <tbody>{cmds.map((c, i) => (<tr key={c.id}><td className="text-light">{i + 1}</td><td className="text-light">{c.name}</td><td className="text-light">{c.path}</td><td><button className="btn btn-sm btn-glow-red" onClick={() => onDelete(c.id)}>Delete</button></td></tr>))}</tbody>
        </table>
      </div>
    </div>
  )
}

function WebCmdSection({ cmds, onAdd, onDelete }: { cmds: WebCmd[]; onAdd: (n: string, u: string) => void; onDelete: (id: number) => void }) {
  const [name, setName] = useState(''); const [url, setUrl] = useState('')
  return (
    <div className="p-2 mt-4">
      <p className="text-white">Web Commands</p>
      <div className="d-flex mt-2 gap-2">
        <input className="form-control glassy-form" placeholder="keyword eg: google" value={name} onChange={e => setName(e.target.value)} />
        <input className="form-control glassy-form" placeholder="url eg: www.google.com" value={url} onChange={e => setUrl(e.target.value)} />
        <button className="btn btn-glow" style={{ width: 'auto', whiteSpace: 'nowrap' }} onClick={() => { if (name && url) { onAdd(name, url); setName(''); setUrl('') } }}>Add</button>
      </div>
      <div className="table-responsive table-scroll mt-3">
        <table className="table"><thead><tr><th className="text-light">#</th><th className="text-light">Keyword</th><th className="text-light">URL</th><th className="text-light">Delete</th></tr></thead>
          <tbody>{cmds.map((c, i) => (<tr key={c.id}><td className="text-light">{i + 1}</td><td className="text-light">{c.name}</td><td className="text-light">{c.url}</td><td><button className="btn btn-sm btn-glow-red" onClick={() => onDelete(c.id)}>Delete</button></td></tr>))}</tbody>
        </table>
      </div>
    </div>
  )
}

function ContactSection({ contacts, onAdd, onDelete }: { contacts: Contact[]; onAdd: (n: string, m: string, e: string, a: string) => void; onDelete: (id: number) => void }) {
  const [form, setForm] = useState({ name: '', mobile_no: '', email: '', address: '' })
  return (
    <div className="p-4">
      <div className="d-flex flex-column gap-2 mb-3">
        {(['name', 'mobile_no', 'email', 'address'] as const).map(f => (
          <input key={f} className="form-control glassy-form" placeholder={f.replace('_', ' ')} value={form[f]} onChange={e => setForm(p => ({ ...p, [f]: e.target.value }))} />
        ))}
        <div className="text-center">
          <button className="btn btn-glow" onClick={() => { if (form.name && form.mobile_no) { onAdd(form.name, form.mobile_no, form.email, form.address); setForm({ name: '', mobile_no: '', email: '', address: '' }) } }}>Add Contact</button>
        </div>
      </div>
      <div className="table-responsive table-scroll">
        <table className="table"><thead><tr><th className="text-light">#</th><th className="text-light">Name</th><th className="text-light">Mobile</th><th className="text-light">Email</th><th className="text-light">Address</th><th className="text-light">Delete</th></tr></thead>
          <tbody>{contacts.map((c, i) => (<tr key={c.id}><td className="text-light">{i + 1}</td><td className="text-light">{c.name}</td><td className="text-light">{c.mobile_no}</td><td className="text-light">{c.email}</td><td className="text-light">{c.address}</td><td><button className="btn btn-sm btn-glow-red" onClick={() => onDelete(c.id)}>Delete</button></td></tr>))}</tbody>
        </table>
      </div>
    </div>
  )
}
