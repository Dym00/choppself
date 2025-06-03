// static/js/index.js

let selectedAmount = 0;
let selectedPaymentMethod = '';
let currentStep = 1;
let cardData = null; // Variável global para armazenar os dados do cartão

document.addEventListener('DOMContentLoaded', function() {
    loadCardData();
    setupTabs();
    setupRechargeModal();
});

function loadCardData() {
    const loading = document.getElementById('loading');
    loading.style.display = 'flex'; // Mostra o spinner de loading
    fetch('/api/card-data')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                cardData = result.data; // Armazena os dados do cartão globalmente
                updateUIWithCardData(cardData);
            } else {
                console.error('Erro ao carregar dados do cartão:', result.message);
                window.location.href = '/card-reader'; // Redireciona se não houver cartão ativo
            }
            loading.style.display = 'none'; // Esconde o spinner de loading
        })
        .catch(error => {
            console.error('Erro:', error);
            loading.style.display = 'none'; // Esconde o spinner em caso de erro
            window.location.href = '/card-reader'; // Redireciona em caso de erro na requisição
        });
}

function updateUIWithCardData(data) {
    // Atualizar avatar e nome
    if (data.name) {
        document.getElementById('user-avatar').textContent = data.name.charAt(0);
        document.getElementById('user-name').textContent = data.name;
    } else {
        document.getElementById('user-avatar').textContent = 'N/A'; // Ou um valor padrão
        document.getElementById('user-name').textContent = 'Nome não disponível';
    }

    // Atualizar CPF
    if (data.cpf) {
        const cpfFormatado = data.cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
        document.getElementById('user-cpf').textContent = cpfFormatado;
    } else {
        document.getElementById('user-cpf').textContent = 'Não informado';
    }

    // Atualizar data de nascimento
    if (data.birth_date) {
        const birthDate = new Date(data.birth_date);
        const dia = String(birthDate.getDate()).padStart(2, '0');
        const mes = String(birthDate.getMonth() + 1).padStart(2, '0');
        const ano = birthDate.getFullYear();
        document.getElementById('user-birth-date').textContent = `${dia}/${mes}/${ano}`;
    } else {
        document.getElementById('user-birth-date').textContent = 'Não informada';
    }

    // Atualizar email, telefone
    document.getElementById('user-email').textContent = data.email || 'Não informado';
    document.getElementById('user-phone').textContent = data.phone || 'Não informado';


    // Atualizar data de cadastro (vem do CLIENTE.DT_CADASTRO)
    if (data.register_date) {
        const registerDate = new Date(data.register_date);
        const dia = String(registerDate.getDate()).padStart(2, '0');
        const mes = String(registerDate.getMonth() + 1).padStart(2, '0');
        const ano = registerDate.getFullYear();
        document.getElementById('user-register-date').textContent = `${dia}/${mes}/${ano}`;
    } else {
        document.getElementById('user-register-date').textContent = 'Não informada';
    }


    // Atualizar número do cartão (agora data.id_cartao)
    const cardNumberElements = document.querySelectorAll('.card-number');
    cardNumberElements.forEach(el => {
        el.textContent = `Cartão Nº ${data.id_cartao}`;
    });

    // Atualizar saldos
    const saldoElements = document.querySelectorAll('.saldo-value');
    saldoElements.forEach(el => {
        el.textContent = `R$ ${data.balance.toFixed(2).replace('.', ',')}`;
    });

    // Atualizar consumo pendente
    document.getElementById('debito-value').textContent = `R$ ${data.pending.toFixed(2).replace('.', ',')}`;

    // Atualizar data de entrada na sessão (entry_date)
    if (data.entry_date) {
        const date = new Date(data.entry_date);
        const dia = String(date.getDate()).padStart(2, '0');
        const mes = String(date.getMonth() + 1).padStart(2, '0');
        const ano = date.getFullYear();
        const horas = String(date.getHours()).padStart(2, '0');
        const minutos = String(date.getMinutes()).padStart(2, '0');
        const dataFormatada = `${dia}/${mes}/${ano} ${horas}:${minutos}`;
        document.getElementById('data-entrada').textContent = dataFormatada;
    } else {
        document.getElementById('data-entrada').textContent = 'Não registrada';
    }
    
    // Atualizar ações do cartão com base no tipo
    updateCardActions(data.type);
}

function updateCardActions(cardType) {
    const actionsContainer = document.getElementById('card-actions');
    actionsContainer.innerHTML = '';
    if (cardType === 'pre') {
        actionsContainer.innerHTML = `
        <button class="btn" onclick="openRechargeModal()">Recarregar Cartão</button>
        <button class="btn btn-outline" onclick="changeTab('cervejas')">Ver Cervejas</button>
        <button class="btn btn-outline" onclick="encerrarSessao()">Encerrar</button>
        <button class="btn btn-outline" onclick="mudarTipo()">Mudar Tipo</button>
        `;
    } else if (cardType === 'pos') {
        actionsContainer.innerHTML = `
        <button class="btn" onclick="confirmarPagamento()">Confirmar Pagamento</button>
        <button class="btn btn-outline" onclick="changeTab('cervejas')">Ver Cervejas</button>
        <button class="btn btn-outline" onclick="encerrarSessao()">Encerrar</button>
        <button class="btn btn-outline" onclick="mudarTipo()">Mudar Tipo</button>
        `;
    } else {
        actionsContainer.innerHTML = `<p>Tipo de cartão desconhecido para ações.</p>`;
    }
}

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            changeTab(tabName);
        });
    });
}

function changeTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

function setupRechargeModal() {
    document.querySelectorAll('.amount-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.amount-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            this.classList.add('selected');
            selectedAmount = parseFloat(this.getAttribute('data-value'));
            document.getElementById('custom-value').value = '';
        });
    });

    document.getElementById('custom-value').addEventListener('input', function() {
        document.querySelectorAll('.amount-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        selectedAmount = parseFloat(this.value) || 0;
    });

    document.querySelectorAll('.payment-method').forEach(method => {
        method.addEventListener('click', function() {
            document.querySelectorAll('.payment-method').forEach(m => {
                m.classList.remove('selected');
            });
            this.classList.add('selected');
            selectedPaymentMethod = this.getAttribute('data-method');
            document.getElementById('btn-payment-next').disabled = false;
        });
    });

    window.addEventListener('click', function(event) {
        const modal = document.getElementById('recharge-modal');
        if (event.target === modal) {
            closeRechargeModal();
        }
    });
}

function openRechargeModal() {
    document.getElementById('recharge-modal').classList.add('active');
    resetModalState();
}

function closeRechargeModal() {
    document.getElementById('recharge-modal').classList.remove('active');
}

function resetModalState() {
    selectedAmount = 0;
    selectedPaymentMethod = '';
    currentStep = 1;
    document.querySelectorAll('.amount-option').forEach(option => {
        option.classList.remove('selected');
    });
    document.querySelectorAll('.payment-method').forEach(method => {
        method.classList.remove('selected');
    });
    document.getElementById('custom-value').value = '';
    document.querySelectorAll('.recharge-step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById('step-valor').classList.add('active');
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
        step.classList.remove('completed');
    });
    document.querySelectorAll('.step')[0].classList.add('active');
    document.getElementById('btn-payment-next').disabled = true;
}

function nextStep(step) {
    if (step === 2) {
        if (selectedAmount <= 0) {
            alert('Por favor, selecione um valor para recarga.');
            return;
        }
    }
    currentStep = step;
    document.querySelectorAll('.step').forEach((stepEl, index) => {
        stepEl.classList.remove('active');
        if (index + 1 < step) {
            stepEl.classList.add('completed');
        } else if (index + 1 === step) {
            stepEl.classList.add('active');
        }
    });
    document.querySelectorAll('.recharge-step').forEach(stepContent => {
        stepContent.classList.remove('active');
    });
    if (step === 2) {
        document.getElementById('step-pagamento').classList.add('active');
    } else if (step === 3) {
        document.getElementById('confirm-value').textContent = `R$ ${selectedAmount.toFixed(2).replace('.', ',')}`;
        let methodText = '';
        switch (selectedPaymentMethod) {
            case 'pix':
                methodText = 'PIX';
                break;
            case 'credit':
                methodText = 'Cartão de Crédito';
                break;
            case 'debit':
                methodText = 'Cartão de Débito';
                break;
        }
        document.getElementById('confirm-method').textContent = methodText;
        document.getElementById('confirm-total').textContent = `R$ ${selectedAmount.toFixed(2).replace('.', ',')}`;
        document.getElementById('step-confirmacao').classList.add('active');
    }
}

function prevStep(step) {
    nextStep(step);
}

function confirmRecharge() {
    document.querySelectorAll('.recharge-step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById('processing-payment').classList.add('active');
    fetch('/api/recharge-card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            amount: selectedAmount
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('new-balance-value').textContent = `R$ ${data.new_balance.toFixed(2).replace('.', ',')}`;
                const saldoElements = document.querySelectorAll('.saldo-value');
                saldoElements.forEach(el => {
                    el.textContent = `R$ ${data.new_balance.toFixed(2).replace('.', ',')}`;
                });
                document.querySelectorAll('.recharge-step').forEach(step => {
                    step.classList.remove('active');
                });
                document.getElementById('payment-success').classList.add('active');
                if (cardData) {
                    cardData.balance = data.new_balance;
                }
            } else {
                alert(`Erro: ${data.message}`);
                closeRechargeModal();
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao processar pagamento. Tente novamente.');
            closeRechargeModal();
        });
}

function confirmarPagamento() {
    const loading = document.getElementById('loading');
    loading.style.display = 'flex';
    fetch('/api/confirm-payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('debito-value').textContent = 'R$ 0,00';
                if (cardData) {
                    cardData.pending = 0.00;
                }
                alert('Pagamento confirmado com sucesso!');
            } else {
                alert(`Erro: ${data.message}`);
            }
            loading.style.display = 'none';
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao confirmar pagamento. Tente novamente.');
            loading.style.display = 'none';
        });
}

function encerrarSessao() {
    if (confirm('Deseja realmente encerrar a sessão?')) {
        const loading = document.getElementById('loading');
        loading.style.display = 'flex';
        fetch('/api/end-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/card-reader';
                } else {
                    alert(`Erro: ${data.message}`);
                    loading.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao encerrar sessão. Tente novamente.');
                loading.style.display = 'none';
            });
    }
}

function mudarTipo() {
    const tipoAtualBackend = cardData.type;
    const novoTipoDisplay = tipoAtualBackend === 'pre' ? 'pós-pago' : 'pré-pago';

    if (confirm(`Deseja mudar para cartão ${novoTipoDisplay}?`)) {
        const loading = document.getElementById('loading');
        loading.style.display = 'flex';
        fetch('/api/change-card-type', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    cardData.type = data.new_type;
                    updateCardActions(cardData.type);
                    alert(`Tipo de cartão alterado para ${novoTipoDisplay} com sucesso!`);
                } else {
                    alert(`Erro: ${data.message}`);
                }
                loading.style.display = 'none';
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao mudar tipo de cartão. Tente novamente.');
                loading.style.display = 'none';
            });
    }
}