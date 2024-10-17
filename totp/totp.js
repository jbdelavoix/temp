let totpKeys = JSON.parse(localStorage.getItem('mytotpsKeys') || "[]")

// ====
// ==== Drag and drop
// ====

const dragDropArea = document.getElementById('drag-drop-area')
dragDropArea.addEventListener('dragover', (event) => {
    event.preventDefault()
    dragDropArea.style.backgroundColor = '#e9ecef'
})

dragDropArea.addEventListener('dragleave', (event) => {
    event.preventDefault()
    dragDropArea.style.backgroundColor = ''
})

dragDropArea.addEventListener('drop', (event) => {
    event.preventDefault()
    dragDropArea.style.backgroundColor = ''
    const files = event.dataTransfer.files
    handleFiles(files)
})

dragDropArea.addEventListener('click', () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = false
    input.addEventListener('change', (event) => {
        const files = event.target.files
        handleFiles(files)
    })
    input.click()
})

function handleFiles(files) {
    // Traitement des fichiers importés
    const file = files[0]
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = function (event) {
            const img = new Image()
            img.src = event.target.result
            img.onload = () => processQrCode(img)
        }
        reader.readAsDataURL(file)
    }
}

// ====
// ==== QR Code
// ====

function processQrCode(image) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = image.width
    canvas.height = image.height
    ctx.drawImage(image, 0, 0)

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const code = jsQR(imageData.data, canvas.width, canvas.height)

    if (code) {
        addTotp(code.data)
    } else {
        alert('QR code invalide')
    }
}

function addTotp(url) {
    const key = parseOtpauthUrl(url)
    totpKeys.push(key)
    localStorage.setItem('mytotpsKeys', JSON.stringify(totpKeys))
    setInterval(() => {
        renderKeys()
    }, 1000)
    renderKeys()
}

function removeTotp(index) {
    totpKeys.splice(index, 1)
    localStorage.setItem('mytotpsKeys', JSON.stringify(totpKeys))
    renderKeys()
}

function parseOtpauthUrl(url) {
    const urlObj = new URL(url.replace("otpauth", "http"))
    const [service, user] = decodeURIComponent(urlObj.pathname).substring(1).split(':')
    const params = new URLSearchParams(urlObj.search)
    const result = {
        type: urlObj.hostname,
        service: service,
        user: user,
        secret: params.get('secret'),
        issuer: params.get('issuer') || service,
        digits: parseInt(params.get('digits')) || 6,
        period: parseInt(params.get('period')) || 30,
    }
    return result
}

function generateTotp(secret, digits = 6, period = 30) {
    return new window.OTPAuth.TOTP({
        algorithm: 'SHA1',
        digits: digits,
        period: period,
        secret: secret
    }).generate()
}

// ====
// ==== Render
// ====

const keysDiv = document.getElementById('keys')

function renderKeys() {
    keysDiv.innerHTML = ''
    totpKeys.forEach((key, index) => {
        keysDiv.innerHTML += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="totp-header">
                            <h2>${key.issuer}</h2>
                            <!-- Bouton pour supprimer la clé -->
                            <button class="delete-btn" onclick="removeTotp(${index})">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                        <div class="totp-subheader">
                            <h3>${key.user}</h3>
                        </div>
                        <!-- Code TOTP et bouton copier -->
                        <div class="totp-code-container">
                            <div class="totp-code" id="totp-${index}">${generateTotp(key.secret, key.digits, key.period)}</div>
                            <button class="copy-btn" onclick="copyToClipboard(${index})">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                </div>`
    })
}

function copyToClipboard(index) {
    const totpCode = document.getElementById(`totp-${index}`).innerText
    navigator.clipboard.writeText(totpCode)
}

// ====
// ==== Manage file
// ====

const openFileButton = document.getElementById('openFile')
const saveFileButton = document.getElementById('saveFile')

async function openFile() {
    const [fileHandle] = await window.showOpenFilePicker({})

    const file = await fileHandle.getFile()
    const content = await file.text()

    totpKeys = JSON.parse(content)
    localStorage.setItem('mytotpsKeys', JSON.stringify(totpKeys))
    renderKeys()
}

async function saveFile() {
    const fileHandle = await window.showSaveFilePicker({
        suggestedName: 'MyTOTPs.mytotps'
    })

    const writableStream = await fileHandle.createWritable()
    await writableStream.write(JSON.stringify(totpKeys))
    await writableStream.close()
}

function init() {
    renderKeys()
}

init()
