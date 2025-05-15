// Script para atualizar dinamicamente a data e hora de entrada
document.addEventListener('DOMContentLoaded', function() {
    // Função para definir a data e hora de entrada
    function setEntryDateTime() {
        // Obter data e hora atual
        const now = new Date();
        
        // Formatar a data no padrão brasileiro
        const dia = String(now.getDate()).padStart(2, '0');
        const mes = String(now.getMonth() + 1).padStart(2, '0');
        const ano = now.getFullYear();
        const horas = String(now.getHours()).padStart(2, '0');
        const minutos = String(now.getMinutes()).padStart(2, '0');
        
        // Montar a string de data e hora formatada
        const dataFormatada = `${dia}/${mes}/${ano} ${horas}:${minutos}`;
        
        // Atualizar o elemento HTML
        document.getElementById('data-entrada').textContent = dataFormatada;
    }
    
    // Definir a data e hora automaticamente ao carregar a página
    setEntryDateTime();
    
    // Adicionar função para simular uma nova entrada de cliente (para demonstração)
    window.atualizarEntrada = function() {
        setEntryDateTime();
        alert('Registro de entrada atualizado!');
    }
    
    // Opcionalmente, podemos adicionar um botão para testar o recurso
    const botaoRecarregar = document.querySelector('button.btn');
    const botaoAtualizar = document.createElement('button');
    botaoAtualizar.className = 'btn btn-outline';
    botaoAtualizar.textContent = 'Atualizar Entrada';
    botaoAtualizar.onclick = window.atualizarEntrada;
    botaoRecarregar.parentNode.appendChild(botaoAtualizar);
});

// Script para o modal de recarga
let selectedAmount = 0;
let selectedPaymentMethod = '';
let currentStep = 1;

// Função para abrir o modal de recarga
function openRechargeModal() {
    document.getElementById('recharge-modal').classList.add('active');
    resetModalState();
}

// Função para fechar o modal de recarga
function closeRechargeModal() {
    document.getElementById('recharge-modal').classList.remove('active');
}

// Função para resetar o estado do modal
function resetModalState() {
    // Resetar variáveis
    selectedAmount = 0;
    selectedPaymentMethod = '';
    currentStep = 1;
    
    // Resetar UI
    document.querySelectorAll('.amount-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    document.querySelectorAll('.payment-method').forEach(method => {
        method.classList.remove('selected');
    });
    
    document.getElementById('custom-value').value = '';
    
    // Mostrar o primeiro passo
    document.querySelectorAll('.recharge-step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById('step-valor').classList.add('active');
    
    // Resetar os indicadores de passos
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
        step.classList.remove('completed');
    });
    document.querySelectorAll('.step')[0].classList.add('active');
    
    // Desabilitar botão de próximo passo do pagamento
    document.getElementById('btn-payment-next').disabled = true;
}

// Função para avançar para o próximo passo
function nextStep(step) {
    // Validações antes de avançar
    if (step === 2) {
        // Verificar se um valor foi selecionado
        if (selectedAmount <= 0) {
            alert('Por favor, selecione um valor para recarga.');
            return;
        }
    }
    
    // Atualizar o passo atual
    currentStep = step;
    
    // Atualizar a UI dos passos
    document.querySelectorAll('.step').forEach((stepEl, index) => {
        stepEl.classList.remove('active');
        
        if (index + 1 < step) {
            stepEl.classList.add('completed');
        } else if (index + 1 === step) {
            stepEl.classList.add('active');
        }
    });
    
    // Esconder todos os passos e mostrar o atual
    document.querySelectorAll('.recharge-step').forEach(stepContent => {
        stepContent.classList.remove('active');
    });
    
    if (step === 2) {
        document.getElementById('step-pagamento').classList.add('active');
    } else if (step === 3) {
        // Atualizar os valores de confirmação
        document.getElementById('confirm-value').textContent = `R$ ${selectedAmount.toFixed(2).replace('.', ',')}`;
        
        let methodText = '';
        switch(selectedPaymentMethod) {
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

// Função para voltar ao passo anterior
function prevStep(step) {
    nextStep(step); // Reutilizamos a mesma função, apenas mudando o valor do passo
}

// Função para confirmar o pagamento e finalizar a recarga
function confirmRecharge() {
    // Mostrar tela de processamento
    document.querySelectorAll('.recharge-step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById('processing-payment').classList.add('active');
    
    // Simular processamento (em um sistema real, aqui seria feita a integração com o gateway de pagamento)
    setTimeout(() => {
        // Atualizar o novo saldo
        const currentBalance = parseFloat(document.querySelector('.saldo-value').textContent.replace('R$ ', '').replace(',', '.'));
        const newBalance = currentBalance + selectedAmount;
        
        // Atualizar o saldo no modal de sucesso
        document.getElementById('new-balance-value').textContent = `R$ ${newBalance.toFixed(2).replace('.', ',')}`;
        
        // Atualizar o saldo em todos os lugares da UI
        document.querySelectorAll('.saldo-value').forEach(el => {
            el.textContent = `R$ ${newBalance.toFixed(2).replace('.', ',')}`;
        });
        
        // Mostrar tela de sucesso
        document.querySelectorAll('.recharge-step').forEach(step => {
            step.classList.remove('active');
        });
        document.getElementById('payment-success').classList.add('active');
        
    }, 2000); // Simula um processamento de 2 segundos
}

// Event listeners para quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Event listener para opções de valor
    document.querySelectorAll('.amount-option').forEach(option => {
        option.addEventListener('click', function() {
            // Remover seleção anterior
            document.querySelectorAll('.amount-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // Adicionar nova seleção
            this.classList.add('selected');
            
            // Atualizar valor selecionado
            selectedAmount = parseFloat(this.getAttribute('data-value'));
            
            // Limpar campo de valor personalizado
            document.getElementById('custom-value').value = '';
        });
    });
    
    // Event listener para valor personalizado
    document.getElementById('custom-value').addEventListener('input', function() {
        // Remover seleção de qualquer opção predefinida
        document.querySelectorAll('.amount-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Atualizar valor selecionado
        selectedAmount = parseFloat(this.value) || 0;
    });
    
    // Event listener para métodos de pagamento
    document.querySelectorAll('.payment-method').forEach(method => {
        method.addEventListener('click', function() {
            // Remover seleção anterior
            document.querySelectorAll('.payment-method').forEach(m => {
                m.classList.remove('selected');
            });
            
            // Adicionar nova seleção
            this.classList.add('selected');
            
            // Atualizar método selecionado
            selectedPaymentMethod = this.getAttribute('data-method');
            
            // Habilitar botão de próximo
            document.getElementById('btn-payment-next').disabled = false;
        });
    });
    
    // Fechar o modal quando clicar fora do conteúdo
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('recharge-modal');
        if (event.target === modal) {
            closeRechargeModal();
        }
    });
});

fetch('/api/saldo')
    .then(res => res.json())
    .then(data => {
        document.querySelector('.saldo-value').textContent = `R$ ${data.saldo.toFixed(2).replace('.', ',')}`;
        document.querySelector('.debito-value').textContent = `R$ ${data.pendente.toFixed(2).replace('.', ',')}`;
    });