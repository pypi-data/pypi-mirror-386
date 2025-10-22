# 🧩 FileShareCLI

**FileShareCLI** is a simple yet powerful Python-based CLI tool that lets developers share files and command snippets effortlessly from the terminal.  
It’s built for developers, workshops, and teams who need a quick, secure way to share files and code — without any setup or cloud dependency.

---

## 🚀 Installation

Install **FileShareCLI** globally via **pip**:

```bash
pip install filesharecli
```

---

## ⚙️ Usage

### 🏗️ Create a New Share Command

To create a new command for your file:

```bash
filesharecli
```

Then follow the prompts:

```
✅ Token loaded successfully!
Do you want to create cmd or read the file (C/R): C
Pick the file name to read the content: 1.txt
```

Once done, you’ll get a shareable command like:

```
Here is your command below to install content:
> pip install filesharecli
> filesharecli read <id>
```

You can now share this `<id>` with anyone — they can retrieve the same file easily.

---

### 📥 Read a Shared File

To view or download a shared file:

```bash
filesharecli read <file_id>
```

Then choose your preferred option:

```
Do you want to see the content or download the content as .txt (see/download): see
```

The file content or a downloadable `.txt` file will be returned instantly.

---

## ⏳ Expiry Policy

All shared file IDs automatically **expire after 7 days** for security and cleanup.  
Once expired, the link or ID will no longer work.

---

## 🧠 Example Workflow

#### Step 1: Create a Share Command
```bash
filesharecli
```
→ Choose **C** (create)  
→ Pick a file, e.g., `1.txt`

#### Step 2: Share Command
```
pip install filesharecli
filesharecli read abc123
```

#### Step 3: Read File (Receiver)
```bash
filesharecli read abc123
```
→ Choose to **see** or **download** content.

---

## 💡 Key Highlights

- ⚡ Share files in seconds directly from CLI  
- 🔒 Auto-expiring file IDs (7 days)  
- 🧠 Simple commands with zero config  
- 💻 Developer-friendly and cross-platform  
- 🌐 Perfect for workshops, meetups, and dev teams  

---

## 🧰 Example Output

```
✅ Token loaded successfully!
Do you want to create cmd or read the file (C/R): C
Pick the file name to read the content: test.txt
📦 Generating command...
✅ Done!
Here is your command below to install content:
> pip install filesharecli
> filesharecli read xyz789
```

---

## 🧪 Coming Soon
- Custom expiry duration  

---

## 🪪 License

MIT License © 2025 [Your Name or Handle]  
All rights reserved.

---

### 🌐 Project Links
- Website: [https://filesharecli.vercel.app](https://filesharecli.vercel.app)
- PyPI: [https://pypi.org/project/filesharecli](https://pypi.org/project/filesharecli)
