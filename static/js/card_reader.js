// static/js/card_reader.js

document.addEventListener('DOMContentLoaded', function() {
    const btnSimulateInactive = document.getElementById('btn-simulate-inactive');
    const btnSimulateActive = document.getElementById('btn-simulate-active');
    const cpfCheckForm = document.getElementById('cpf-check-form');
    const inactiveCardForm = document.getElementById('inactive-card-form');
    const btnCheckCpf = document.getElementById('btn-check-cpf');
    const btnActivateCard = document.getElementById('btn-activate-card');
    const cardNumberContainer = document.getElementById('card-number-container');
    const cardNumberContainerCpf = document.getElementById('card-number-container-cpf');
    const loading = document.getElementById('loading');
    const clientCpfCheck = document.getElementById('client-cpf-check');
    const clientCpf = document.getElementById('client-cpf');
    const clientBirthDate = document.getElementById('client-birth-date');

    let currentCardNumber = null;

    // Função para formatar CPF
    function formatarCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');
        if (cpf.length > 11) cpf = cpf.substring(0, 11);
        if (cpf.length > 9) {
            cpf = cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
        } else if (cpf.length > 6) {
            cpf = cpf.replace(/(\d{3})(\d{3})(\d{1,3})/, "$1.$2.$3");
        } else if (cpf.length > 3) {
            cpf = cpf.replace(/(\d{3})(\d{1,3})/, "$1.$2");
        }
        return cpf;
    }

    // Aplicar formatação de CPF nos campos
    clientCpfCheck.addEventListener('input', function() {
        this.value = formatarCPF(this.value);
    });

    clientCpf.addEventListener('input', function() {
        this.value = formatarCPF(this.value);
    });

    // Função para validar CPF (implementação básica)
    function validarCPF(cpf) {
        cpf = cpf.replace(/[^\d]+/g, '');
        if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
        return true;
    }

    // Função para validar data de nascimento (18 anos)
    function validarIdade(dataNascimento) {
        const hoje = new Date();
        const nascimento = new Date(dataNascimento);
        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const m = hoje.getMonth() - nascimento.getMonth();

        if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) {
            idade--;
        }

        return idade >= 18;
    }

    btnSimulateInactive.addEventListener('click', function() {
        loading.style.display = 'flex';
        fetch('/api/generate-card-number')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentCardNumber = data.card_number;
                    cpfCheckForm.style.display = 'block';
                    document.querySelector('.card-reader-message').style.display = 'none';
                    document.querySelector('.simulation-buttons').style.display = 'none';
                    cardNumberContainerCpf.innerHTML = `<strong>Número do Cartão: ${currentCardNumber.toString().padStart(4, '0')}</strong>`;
                } else {
                    alert('Erro ao gerar número de cartão. Tente novamente.');
                }
                loading.style.display = 'none';
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com o servidor. Tente novamente.');
                loading.style.display = 'none';
            });
    });

    btnSimulateActive.addEventListener('click', function() {
        loading.style.display = 'flex';
        fetch('/api/simulate-active-card')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/';
                } else {
                    alert(`Erro ao simular cartão ativo: ${data.message}. Tente novamente.`);
                }
                loading.style.display = 'none';
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com o servidor. Tente novamente.');
                loading.style.display = 'none';
            });
    });

    btnCheckCpf.addEventListener('click', function() {
        const cpf = document.getElementById('client-cpf-check').value;

        if (!cpf) {
            alert('Por favor, informe o CPF do cliente.');
            return;
        }

        if (!validarCPF(cpf)) {
            alert('CPF inválido. Por favor, verifique.');
            return;
        }

        if (!currentCardNumber) {
            alert('Erro: Número de cartão não encontrado. Tente novamente.');
            return;
        }

        loading.style.display = 'flex';

        fetch('/api/check-client', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cpf: cpf,
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.client_exists) {
                        window.location.href = '/';
                    } else {
                        cpfCheckForm.style.display = 'none';
                        inactiveCardForm.style.display = 'block';
                        cardNumberContainer.innerHTML = `<strong>Número do Cartão: ${currentCardNumber.toString().padStart(4, '0')}</strong>`;
                        document.getElementById('client-cpf').value = cpf;
                    }
                } else {
                    alert(`Erro: ${data.message}`);
                }
                loading.style.display = 'none';
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com o servidor. Tente novamente.');
                loading.style.display = 'none';
            });
    });

    btnActivateCard.addEventListener('click', function() {
        const cpf = document.getElementById('client-cpf').value;
        const name = document.getElementById('client-name').value;
        const email = document.getElementById('client-email').value;
        const phone = document.getElementById('client-phone').value;
        const cardType = document.getElementById('card-type').value;
        const birthDate = clientBirthDate.value;

        if (!cpf || !name || !email || !phone || !birthDate) {
            alert('Por favor, preencha todos os campos obrigatórios!');
            return;
        }

        if (!validarCPF(cpf)) {
            alert('CPF inválido. Por favor, verifique.');
            return;
        }

        if (!currentCardNumber) {
            alert('Erro: Número de cartão não encontrado. Tente simular um cartão inativo primeiro.');
            return;
        }

        if (!validarIdade(birthDate)) {
            alert('Erro: Cliente deve ter pelo menos 18 anos.');
            return;
        }

        loading.style.display = 'flex';
        const cardData = {
            cpf: cpf,
            name: name,
            email: email,
            phone: phone,
            card_type: cardType,
            card_number: currentCardNumber,
            birth_date: birthDate
        };

        fetch('/api/activate-card', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cardData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.redirect) {
                        window.location.href = '/';
                    } else {
                        alert('Cartão ativado e cliente cadastrado com sucesso!');
                        window.location.href = '/';
                    }
                } else {
                    alert(`Erro: ${data.message}`);
                }
                loading.style.display = 'none';
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com o servidor. Tente novamente.');
                loading.style.display = 'none';
            });
    });
});