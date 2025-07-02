import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import { Button } from '../../Producao/components/ui/button';
import { fetchComAuth } from '../../../utils/fetchComAuth';

const currency = v => Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function Negociacao() {
  const { id, tarefaId } = useParams();
  const navigate = useNavigate();
  const [pontuacao, setPontuacao] = useState('4');
  const [condicoes, setCondicoes] = useState([]);
  const [condicaoId, setCondicaoId] = useState('');
  const [desc1, setDesc1] = useState('');
  const [desc2, setDesc2] = useState('');
  const [entrada, setEntrada] = useState('');
  const [numParcelas, setNumParcelas] = useState('');
  const [ambientes, setAmbientes] = useState([]);
  const [selecionados, setSelecionados] = useState({});
  const [custos, setCustos] = useState([]);
  const [novoCusto, setNovoCusto] = useState({ descricao: '', ambiente: '', valor: '' });
  const [mostrarFormCusto, setMostrarFormCusto] = useState(false);
  const [mostrarListaCustos, setMostrarListaCustos] = useState(false);
  const [editIdx, setEditIdx] = useState(-1);
  const [parcelas, setParcelas] = useState([]);
  const [totalVenda, setTotalVenda] = useState(0);
  const [atendimento, setAtendimento] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [templateId, setTemplateId] = useState('');

  useEffect(() => {
    const carregar = async () => {
      const at = await fetchComAuth(`/comercial/atendimentos/${id}`);
      setAtendimento(at.atendimento);
      const t = await fetchComAuth(`/comercial/atendimentos/${id}/tarefas`);
      const conds = await fetchComAuth('/comercial/condicoes-pagamento');
      const temps = await fetchComAuth('/comercial/templates?tipo=orcamento');
      setCondicoes(conds.condicoes || []);
      setTemplates(temps.templates || []);
      const proj = t.tarefas.find(tt => tt.nome === 'Projeto 3D');
      const orcAtual = t.tarefas.find(tt => String(tt.id) === String(tarefaId));
      let dadosProj = {};
      let dadosNeg = {};
      try { dadosProj = proj && proj.dados ? JSON.parse(proj.dados) : {}; } catch (e) { /* ignore */ }
      try { dadosNeg = orcAtual && orcAtual.dados ? JSON.parse(orcAtual.dados) : {}; } catch (e) { /* ignore */ }
      const projs = (at.atendimento.projetos || '').split(',').map(p => p.trim()).filter(Boolean);
      const listaAmb = projs.map(a => ({
        nome: a,
        valor: dadosProj.projetos?.[a]?.total || dadosProj.projetos?.[a]?.valor || 0
      }));
      setAmbientes(listaAmb);
      setSelecionados(listaAmb.reduce((acc, a) => ({ ...acc, [a.nome]: true }), {}));
      if (dadosNeg.pontuacao) setPontuacao(String(dadosNeg.pontuacao));
      if (dadosNeg.condicaoId) setCondicaoId(String(dadosNeg.condicaoId));
      if (dadosNeg.desconto1) setDesc1(String(dadosNeg.desconto1));
      if (dadosNeg.desconto2) setDesc2(String(dadosNeg.desconto2));
      if (dadosNeg.entrada) setEntrada(String(dadosNeg.entrada));
      if (dadosNeg.numParcelas) setNumParcelas(String(dadosNeg.numParcelas));
      if (dadosNeg.custos) setCustos(dadosNeg.custos);
    };
    carregar();
  }, [id, tarefaId]);

  const toggleAmb = nome => {
    setSelecionados(prev => ({ ...prev, [nome]: !prev[nome] }));
  };

  const addCusto = () => {
    if (!novoCusto.descricao || !novoCusto.ambiente || !novoCusto.valor) return;
    if (editIdx >= 0) {
      setCustos(prev => prev.map((c, i) => (i === editIdx ? { ...novoCusto, valor: parseFloat(novoCusto.valor) } : c)));
      setEditIdx(-1);
    } else {
      setCustos(prev => [...prev, { ...novoCusto, valor: parseFloat(novoCusto.valor) }]);
    }
    setNovoCusto({ descricao: '', ambiente: '', valor: '' });
    setMostrarFormCusto(false);
  };

  const somaCustos = nome => custos.filter(c => c.ambiente === nome).reduce((s, c) => s + Number(c.valor || 0), 0);
  const valorAmbiente = nome => {
    const amb = ambientes.find(a => a.nome === nome);
    return (amb?.valor || 0) + somaCustos(nome);
  };

  const editarCusto = idx => {
    const c = custos[idx];
    setNovoCusto({ descricao: c.descricao, ambiente: c.ambiente, valor: c.valor });
    setEditIdx(idx);
    setMostrarFormCusto(true);
  };

  const removerCusto = idx => {
    setCustos(prev => prev.filter((_, i) => i !== idx));
  };

  const valorOrcamento = nome => {
    let v = valorAmbiente(nome);
    if (pontuacao) v *= parseFloat(pontuacao);
    if (desc1) v *= 1 - parseFloat(desc1) / 100;
    if (desc2) v *= 1 - parseFloat(desc2) / 100;
    if (total > 0) v *= totalVenda / total;
    return v;
  };

  const totalBase = ambientes.reduce((s, a) => s + (selecionados[a.nome] ? valorAmbiente(a.nome) : 0), 0);
  let total = totalBase;
  if (pontuacao) total *= parseFloat(pontuacao);
  if (desc1) total *= 1 - parseFloat(desc1) / 100;
  if (desc2) total *= 1 - parseFloat(desc2) / 100;

  useEffect(() => {
    const c = condicoes.find(cc => String(cc.id) === String(condicaoId));
    if (!c) {
      setParcelas([]);
      setTotalVenda(total);
      return;
    }

    const temEntrada = parseFloat(entrada || 0) > 0;
    const tipo = temEntrada ? 'com' : 'sem';
    const listaOrig = c.parcelas?.[tipo] || [];
    const lista = [...listaOrig].sort((a, b) => (a.numero || 0) - (b.numero || 0));

    const max = c.numero_parcelas || (c.parcelas ? c.parcelas.sem.length + c.parcelas.com.length : 0);
    const nSel = numParcelas ? parseInt(numParcelas, 10) : max;
    const nCalculo = temEntrada ? nSel - 1 : nSel;
    const resto = total - parseFloat(entrada || 0);
    const valorBase = nCalculo > 0 ? resto / nCalculo : 0;

    let listaParcelas = lista.slice(0, Math.max(nCalculo, 0)).map((p, idx) => {
      const juros = parseFloat(p.retencao || 0) / 100;
      const valor = valorBase * (1 + juros);
      const numero = temEntrada ? idx + 2 : idx + 1;
      return { numero, valor };
    });

    if (temEntrada) {
      listaParcelas = [{ numero: 1, valor: parseFloat(entrada) || 0 }, ...listaParcelas];
    }

    setParcelas(listaParcelas);
    const soma = listaParcelas.reduce((s, p) => s + Number(p.valor || 0), 0);
    setTotalVenda(soma);
  }, [condicaoId, total, condicoes, numParcelas, entrada]);

  const salvar = async () => {
    const descricao = parcelas
      .map(p => `Parcela ${p.numero} = R$ ${currency(p.valor)}`)
      .join(', ');
    const condNome = condicoes.find(c => String(c.id) === String(condicaoId))?.nome || '';
    const dados = {
      pontuacao,
      condicaoId,
      condicaoNome: condNome,
      entrada,
      numParcelas,
      desconto1: desc1,
      desconto2: desc2,
      custos,
      ambientes,
      selecionados,
      parcelas,
      descricao_pagamento: descricao,
      total: totalVenda || total,
    };
    await fetchComAuth(`/comercial/atendimentos/${id}/tarefas/${tarefaId}`, {
      method: 'PUT',
      body: JSON.stringify({ concluida: true, dados: JSON.stringify(dados) }),
    });
    navigate(`/comercial/${id}`);
  };

  const visualizarOrcamento = async () => {
    let tplId = templateId;
    if (!tplId) {
      if (templates.length === 0) {
        alert('Nenhum template cadastrado');
        return;
      }
      if (templates.length === 1) {
        tplId = templates[0].id;
      } else {
        const opcoes = templates.map((t, i) => `${i + 1} - ${t.titulo}`).join('\n');
        const escolha = window.prompt(`Selecione o template:\n${opcoes}`);
        if (!escolha) return;
        const idx = parseInt(escolha, 10) - 1;
        if (!templates[idx]) return;
        tplId = templates[idx].id;
      }
      setTemplateId(tplId);
    }
    const t = await fetchComAuth(`/comercial/templates/${tplId}`);
    const template = t.template;
    if (!template) return;
    const empresa = JSON.parse(localStorage.getItem('empresa') || '{}');

    const footerText = () => {
      switch (template.tipo) {
        case 'contrato':
          return `Contrato ${new Date().getFullYear()}/0001`;
        case 'orcamento':
          return `OR ${atendimento?.codigo || 'AT-0000'} 001`;
        case 'pedido':
          return `Pedido ${atendimento?.codigo || 'AT-0000'}`;
        case 'romaneio':
          return 'Romaneio Nº 00001';
        default:
          return '';
      }
    };
    const cond = condicoes.find(c => String(c.id) === String(condicaoId))?.nome || '';
    const valores = {
      atendimento: atendimento || {},
      empresa,
      negociacao: {
        pontuacao,
        desconto1: desc1,
        desconto2: desc2,
        entrada,
        numParcelas,
        condicao: cond,
        total: totalVenda || total,
        descricao_pagamento: parcelas.map(p => `Parcela ${p.numero} = R$ ${currency(p.valor)}`).join(', '),
      },
    };

    const getValor = caminho => {
      if (!caminho) return '';
      const [grp, campo] = caminho.split('.');
      return valores[grp]?.[campo] ?? '';
    };

    const cont = document.createElement('div');
    cont.style.position = 'fixed';
    cont.style.left = '-10000px';
    cont.className = 'p-4 flex justify-center';
    document.body.appendChild(cont);

    const content = document.createElement('div');
    content.className = 'border bg-white p-4 flex flex-col';
    content.style.width = '210mm';
    content.style.minHeight = '297mm';
    cont.appendChild(content);

    const header = document.createElement('div');
    header.className = 'flex justify-between items-center mb-4';
    if (empresa.logo) {
      const img = document.createElement('img');
      img.src = empresa.logo;
      img.style.height = '40px';
      header.appendChild(img);
    }
    const slog = document.createElement('div');
    slog.textContent = empresa.slogan || '';
    header.appendChild(slog);
    content.appendChild(header);

    const main = document.createElement('div');
    content.appendChild(main);

    const title = document.createElement('h2');
    title.className = 'text-center font-bold mb-4';
    title.textContent = template.titulo;
    main.appendChild(title);

    const wrapper = document.createElement('div');
    wrapper.className = 'flex flex-wrap';
    main.appendChild(wrapper);

    template.campos.forEach(campo => {
      if (campo.tipo === 'section') {
        const sec = document.createElement('div');
        sec.className = 'w-full font-bold pt-4';
        sec.textContent = campo.label || '';
        if (campo.textAlign) sec.style.textAlign = campo.textAlign;
        if (campo.fontSize) sec.style.fontSize = campo.fontSize + 'px';
        wrapper.appendChild(sec);
        return;
      }
      if (campo.tipo === 'separator') {
        const sep = document.createElement('div');
        sep.className = 'w-full px-2 my-2';
        if (campo.textAlign) sep.style.textAlign = campo.textAlign;
        if (campo.fontSize) sep.style.fontSize = campo.fontSize + 'px';
        wrapper.appendChild(sep);
        return;
      }
      const div = document.createElement('div');
      div.className = campo.largura === 'half' ? 'w-1/2 px-2 flex items-center' : 'w-full px-2 flex items-center';
      if (campo.textAlign) div.style.textAlign = campo.textAlign;
      if (campo.fontSize) div.style.fontSize = campo.fontSize + 'px';
      if (campo.tipo === 'titulo') {
        const h = document.createElement('h3');
        h.className = 'font-semibold';
        h.textContent = campo.label || '';
        div.appendChild(h);
      } else if (campo.tipo === 'texto') {
        const t = document.createElement('div');
        t.className = 'whitespace-pre-wrap';
        t.textContent = campo.texto || '';
        div.appendChild(t);
      } else if (campo.tipo === 'table') {
        const table = document.createElement('table');
        table.className = 'pdf-table';
        const thead = document.createElement('thead');
        const trh = document.createElement('tr');
        const thb = document.createElement('th');
        thb.className = 'border px-1 text-center align-middle';
        trh.appendChild(thb);
        for (let i = 0; i < (campo.colunas || 0); i++) {
          const th = document.createElement('th');
          th.className = 'border px-1 text-center align-middle';
          th.textContent = campo.headersColunas?.[i] || '';
          trh.appendChild(th);
        }
        thead.appendChild(trh);
        table.appendChild(thead);
        const tbody = document.createElement('tbody');
        for (let r = 0; r < (campo.linhas || 0); r++) {
          const tr = document.createElement('tr');
          const th = document.createElement('th');
          th.className = 'border px-1 text-center align-middle';
          th.textContent = campo.headersLinhas?.[r] || '';
          tr.appendChild(th);
          for (let cIdx = 0; cIdx < (campo.colunas || 0); cIdx++) {
            const td = document.createElement('td');
            td.className = 'border px-1 text-center align-middle';
            const val = getValor(campo.celulas?.[r]?.[cIdx]?.autoCampo);
            td.textContent = val;
            tr.appendChild(td);
          }
          tbody.appendChild(tr);
        }
        table.appendChild(tbody);
        div.appendChild(table);
      } else if (campo.tipo === 'negociacao') {
        const wrapNeg = document.createElement('div');
        wrapNeg.className = 'text-sm';

        const infoTable = document.createElement('table');
        infoTable.className = 'pdf-table';
        infoTable.style.margin = '24px 0';
        infoTable.style.width = '90%';
        const infoBody = document.createElement('tbody');

        const addRow = (label, value) => {
          const tr = document.createElement('tr');
          const th = document.createElement('th');
          th.className = 'text-left';
          th.textContent = label;
          const td = document.createElement('td');
          td.className = 'border';
          td.textContent = value;
          tr.appendChild(th);
          tr.appendChild(td);
          infoBody.appendChild(tr);
        };

        addRow('Condição de Pagamento', valores.negociacao.condicao || '');
        addRow('Entrada (R$)', `R$ ${currency(valores.negociacao.entrada)}`);
        addRow('Parcelas', valores.negociacao.numParcelas || '');
        infoTable.appendChild(infoBody);
        wrapNeg.appendChild(infoTable);

        const tableProj = document.createElement('table');
        tableProj.className = 'pdf-table';
        const thdP = document.createElement('thead');
        const trP = document.createElement('tr');
        ['Ambiente', 'Orçamento'].forEach(tx => {
          const th = document.createElement('th');
          th.className = 'border px-2 text-center align-middle';
          th.textContent = tx;
          trP.appendChild(th);
        });
        thdP.appendChild(trP);
        tableProj.appendChild(thdP);
        const tbP = document.createElement('tbody');
        ambientes.forEach(a => {
          if (!selecionados[a.nome]) return;
          const tr = document.createElement('tr');
          const tdN = document.createElement('td');
          tdN.className = 'border px-2 text-left align-middle';
          tdN.textContent = a.nome;
          const tdV = document.createElement('td');
          tdV.className = 'border px-2 text-right align-middle';
          tdV.textContent = `R$ ${currency(valorOrcamento(a.nome))}`;
          tr.appendChild(tdN);
          tr.appendChild(tdV);
          tbP.appendChild(tr);
        });
        tableProj.appendChild(tbP);
        wrapNeg.appendChild(tableProj);

        const table = document.createElement('table');
        table.className = 'pdf-table';
        const thead2 = document.createElement('thead');
        const tr2 = document.createElement('tr');
        ['Número', 'Valor'].forEach(tx => {
          const th = document.createElement('th');
          th.className = 'border px-2 text-center align-middle';
          th.textContent = tx;
          tr2.appendChild(th);
        });
        thead2.appendChild(tr2);
        table.appendChild(thead2);
        const tbody2 = document.createElement('tbody');
        parcelas.forEach(p => {
          const tr = document.createElement('tr');
          const tdNum = document.createElement('td');
          tdNum.className = 'border px-2 text-center align-middle';
          tdNum.textContent = p.numero;
          const tdVal = document.createElement('td');
          tdVal.className = 'border px-2 text-right align-middle';
          tdVal.textContent = `R$ ${currency(p.valor)}`;
          tr.appendChild(tdNum);
          tr.appendChild(tdVal);
          tbody2.appendChild(tr);
        });
        table.appendChild(tbody2);
        wrapNeg.appendChild(table);

        const tot = document.createElement('div');
        tot.className = 'text-right font-bold';
        tot.textContent = `Total: R$ ${currency(totalVenda || total)}`;
        wrapNeg.appendChild(tot);

        div.appendChild(wrapNeg);
      } else if (campo.tipo === 'assinatura') {
        const ass = document.createElement('div');
        ass.className = 'text-center mt-4';
        ass.textContent = `${valores.atendimento.cliente || ''} / ${valores.empresa.nomeFantasia || ''}`;
        const line = document.createElement('div');
        line.style.marginTop = '40px';
        line.textContent = '______________________________';
        div.appendChild(line);
        div.appendChild(ass);
      } else if (campo.autoCampo === 'negociacao.tabela') {
        const wrapNeg = document.createElement('div');
        wrapNeg.className = 'text-sm';

        const infoTable = document.createElement('table');
        infoTable.className = 'pdf-table';
        infoTable.style.margin = '24px 0';
        infoTable.style.width = '90%';
        const infoBody = document.createElement('tbody');

        const addRow = (label, value) => {
          const tr = document.createElement('tr');
          const th = document.createElement('th');
          th.className = 'text-left';
          th.textContent = label;
          const td = document.createElement('td');
          td.className = 'border';
          td.textContent = value;
          tr.appendChild(th);
          tr.appendChild(td);
          infoBody.appendChild(tr);
        };

        addRow('Condição de Pagamento', valores.negociacao.condicao || '');
        if (valores.negociacao.entrada) {
          addRow('Entrada (R$)', `R$ ${currency(valores.negociacao.entrada)}`);
        }
        if (valores.negociacao.numParcelas) {
          addRow('Parcelas', valores.negociacao.numParcelas);
        }
        infoTable.appendChild(infoBody);
        wrapNeg.appendChild(infoTable);

        const tableAmb = document.createElement('table');
        tableAmb.className = 'pdf-table';
        const theadAmb = document.createElement('thead');
        const trAmb = document.createElement('tr');
        ['Ambiente', 'Orçamento'].forEach(tx => {
          const th = document.createElement('th');
          th.className = 'border px-2 text-center align-middle';
          th.textContent = tx;
          trAmb.appendChild(th);
        });
        theadAmb.appendChild(trAmb);
        tableAmb.appendChild(theadAmb);
        const tbodyAmb = document.createElement('tbody');
        ambientes.forEach(a => {
          if (!selecionados[a.nome]) return;
          const tr = document.createElement('tr');
          const tdN = document.createElement('td');
          tdN.className = 'border px-2 text-left align-middle';
          tdN.textContent = a.nome;
          const tdV = document.createElement('td');
          tdV.className = 'border px-2 text-right align-middle';
          tdV.textContent = `R$ ${currency(valorOrcamento(a.nome))}`;
          tr.appendChild(tdN);
          tr.appendChild(tdV);
          tbodyAmb.appendChild(tr);
        });
        tableAmb.appendChild(tbodyAmb);
        wrapNeg.appendChild(tableAmb);

        const tablePar = document.createElement('table');
        tablePar.className = 'pdf-table';
        const theadPar = document.createElement('thead');
        const trPar = document.createElement('tr');
        ['Número', 'Valor'].forEach(tx => {
          const th = document.createElement('th');
          th.className = 'border px-2 text-center align-middle';
          th.textContent = tx;
          trPar.appendChild(th);
        });
        theadPar.appendChild(trPar);
        tablePar.appendChild(theadPar);
        const tbodyPar = document.createElement('tbody');
        parcelas.forEach(p => {
          const tr = document.createElement('tr');
          const tdNum = document.createElement('td');
          tdNum.className = 'border px-2 text-center align-middle';
          tdNum.textContent = p.numero;
          const tdVal = document.createElement('td');
          tdVal.className = 'border px-2 text-right align-middle';
          tdVal.textContent = `R$ ${currency(p.valor)}`;
          tr.appendChild(tdNum);
          tr.appendChild(tdVal);
          tbodyPar.appendChild(tr);
        });
        tablePar.appendChild(tbodyPar);
        wrapNeg.appendChild(tablePar);

        const tot = document.createElement('div');
        tot.className = 'text-right font-bold';
        tot.textContent = `Total: R$ ${currency(totalVenda || total)}`;
        wrapNeg.appendChild(tot);

        div.appendChild(wrapNeg);
      } else if (campo.autoCampo === 'empresa.dados_completos') {
        const bloco = document.createElement('div');
        bloco.className = 'space-y-1';
        const l1 = document.createElement('div');
        l1.textContent = empresa.nomeFantasia || 'Empresa LTDA';
        const l2 = document.createElement('div');
        l2.textContent = `${empresa.cnpj || '00.000.000/0000-00'} / ${empresa.inscricaoEstadual || 'IE'}`;
        const l3 = document.createElement('div');
        l3.textContent = `${empresa.rua || 'Rua'}, ${empresa.numero || '123'} - ${empresa.bairro || ''}`;
        const l4 = document.createElement('div');
        l4.textContent = `${empresa.cidade || ''} - ${empresa.estado || ''}`;
        const l5 = document.createElement('div');
        l5.textContent = empresa.telefone1 || '';
        [l1, l2, l3, l4, l5].forEach(el => bloco.appendChild(el));
        div.appendChild(bloco);
      } else if (campo.autoCampo === 'empresa.cabecalho') {
        const bloco = document.createElement('div');
        bloco.className = 'space-y-1';
        const l1 = document.createElement('div');
        l1.textContent = empresa.razaoSocial || 'Empresa LTDA';
        const l2 = document.createElement('div');
        l2.textContent = `CNPJ: ${empresa.cnpj || ''}`;
        const l3 = document.createElement('div');
        l3.textContent = `${empresa.rua || ''}, ${empresa.numero || ''}${empresa.complemento ? ' - ' + empresa.complemento : ''}`;
        const l4 = document.createElement('div');
        l4.textContent = `${empresa.bairro || ''} - ${empresa.cidade || ''}/${empresa.estado || ''}`;
        const l5 = document.createElement('div');
        l5.textContent = `CEP ${empresa.cep || ''}`;
        const l6 = document.createElement('div');
        l6.textContent = `Contato ${empresa.telefone1 || ''}`;
        [l1, l2, l3, l4, l5, l6].forEach(el => bloco.appendChild(el));
        div.appendChild(bloco);
      } else if (campo.autoCampo === 'cliente.cabecalho_com_cpf' || campo.autoCampo === 'cliente.cabecalho_sem_cpf') {
        const cli = valores.atendimento || {};
        const bloco = document.createElement('div');
        bloco.className = 'space-y-1';
        const l1 = document.createElement('div');
        l1.textContent = cli.cliente || cli.nome || '';
        if (campo.autoCampo === 'cliente.cabecalho_com_cpf') {
          const lcpf = document.createElement('div');
          lcpf.textContent = `CPF: ${cli.documento || ''}`;
          bloco.appendChild(lcpf);
        }
        const l3 = document.createElement('div');
        l3.textContent = `${cli.rua || cli.endereco || ''}, ${cli.numero || ''}${cli.complemento ? ' - ' + cli.complemento : ''}`;
        const l4 = document.createElement('div');
        l4.textContent = `${cli.bairro || ''} - ${cli.cidade || ''}/${cli.estado || ''}`;
        const l5 = document.createElement('div');
        l5.textContent = `CEP ${cli.cep || ''}`;
        const l6 = document.createElement('div');
        l6.textContent = `Contato ${cli.telefone || cli.telefone1 || ''}`;
        [l1, l3, l4, l5, l6].forEach(el => bloco.appendChild(el));
        div.appendChild(bloco);
      } else {
        const texto = document.createElement('div');
        texto.className = 'whitespace-pre-wrap';
        const val = campo.autoCampo ? getValor(campo.autoCampo) : '';
        texto.textContent = campo.label ? `${campo.label}: ${val}` : val;
        div.appendChild(texto);
      }
      wrapper.appendChild(div);
    });

    const footer = document.createElement('div');
    footer.className = 'flex justify-between items-center mt-4 text-sm';
    const pag = document.createElement('div');
    pag.textContent = 'Página 1 de 1';
    const foot = document.createElement('div');
    foot.textContent = footerText();
    footer.appendChild(pag);
    footer.appendChild(foot);
    content.appendChild(footer);

    html2canvas(content).then(canvas => {
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      const url = pdf.output('bloburl');
      window.open(url, '_blank');
      document.body.removeChild(cont);
    });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Negociação</h3>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <label className="block">
          <span className="text-sm">Pontuação</span>
          <input type="number" className="input" value={pontuacao} onChange={e => setPontuacao(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Desconto 1 (%)</span>
          <input type="number" className="input" value={desc1} onChange={e => setDesc1(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Desconto 2 (%)</span>
          <input type="number" className="input" value={desc2} onChange={e => setDesc2(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Condição de Pagamento</span>
          <select className="input" value={condicaoId} onChange={e => setCondicaoId(e.target.value)}>
            <option value="">Selecione</option>
            {condicoes.map(c => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm">Entrada (R$)</span>
          <input type="number" className="input" value={entrada} onChange={e => setEntrada(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm">Parcelas</span>
          <select className="input" value={numParcelas} onChange={e => setNumParcelas(e.target.value)}>
            <option value="">Selecione</option>
            {(() => {
              const c = condicoes.find(cc => String(cc.id) === String(condicaoId));
              const n = c ? c.numero_parcelas || (c.parcelas ? c.parcelas.sem.length + c.parcelas.com.length : 0) : 0;
              return Array.from({ length: n }, (_, i) => i + 1).map(nPar => (
                <option key={nPar} value={nPar}>{nPar}</option>
              ));
            })()}
          </select>
        </label>
      </div>
      <div>
        <table className="w-full text-sm mb-2">
          <thead>
            <tr className="bg-gray-100">
              <th className="border px-2"></th>
              <th className="border px-2">Ambiente</th>
              <th className="border px-2">Custo Fábrica</th>
              <th className="border px-2">Custos Adicionais</th>
              <th className="border px-2">Custo Total</th>
              <th className="border px-2">Orçamento</th>
            </tr>
          </thead>
          <tbody>
            {ambientes.map(a => (
              <tr key={a.nome}>
                <td className="border px-2 text-center">
                  <input type="checkbox" checked={selecionados[a.nome] || false} onChange={() => toggleAmb(a.nome)} />
                </td>
                <td className="border px-2">{a.nome}</td>
                <td className="border px-2">{currency(a.valor)}</td>
                <td className="border px-2">{currency(somaCustos(a.nome))}</td>
                <td className="border px-2">{currency(valorAmbiente(a.nome))}</td>
                <td className="border px-2">{currency(valorOrcamento(a.nome))}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex gap-2 mb-2">
          <Button size="sm" variant="secondary" onClick={() => setMostrarFormCusto(!mostrarFormCusto)}>
            {editIdx >= 0 ? 'Editar Custo' : 'Inserir Custos Adicionais'}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setMostrarListaCustos(!mostrarListaCustos)}>
            Listar Custos Adicionais
          </Button>
        </div>
        {mostrarFormCusto && (
          <div className="border p-2 rounded mt-2 space-y-2">
            <label className="block">
              <span className="text-sm">Descrição</span>
              <input className="input" value={novoCusto.descricao} onChange={e => setNovoCusto({ ...novoCusto, descricao: e.target.value })} />
            </label>
            <label className="block">
              <span className="text-sm">Ambiente</span>
              <select className="input" value={novoCusto.ambiente} onChange={e => setNovoCusto({ ...novoCusto, ambiente: e.target.value })}>
                <option value="">Selecione</option>
                {ambientes.map(a => (
                  <option key={a.nome} value={a.nome}>{a.nome}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-sm">Valor (R$)</span>
              <input type="number" className="input" value={novoCusto.valor} onChange={e => setNovoCusto({ ...novoCusto, valor: e.target.value })} />
            </label>
            <Button size="sm" onClick={addCusto}>{editIdx >= 0 ? 'Salvar' : 'Adicionar'}</Button>
          </div>
        )}
        {mostrarListaCustos && (
          <div className="border p-2 rounded mt-2">
            <table className="w-full text-sm mb-2">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-2">Descrição</th>
                  <th className="border px-2">Ambiente</th>
                  <th className="border px-2">Valor</th>
                  <th className="border px-2">Ações</th>
                </tr>
              </thead>
              <tbody>
                {custos.map((c, idx) => (
                  <tr key={idx}>
                    <td className="border px-2">{c.descricao}</td>
                    <td className="border px-2">{c.ambiente}</td>
                    <td className="border px-2">{currency(c.valor)}</td>
                    <td className="border px-2 space-x-2">
                      <button className="text-blue-600" onClick={() => editarCusto(idx)}>Editar</button>
                      <button className="text-red-600" onClick={() => removerCusto(idx)}>Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="flex flex-col md:flex-row gap-4">
        <div className="md:w-1/2">
          <h4 className="font-medium">Parcelas</h4>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-2">Número</th>
                <th className="border px-2">Valor</th>
              </tr>
            </thead>
            <tbody>
              {parcelas.map(p => (
                <tr key={p.numero}>
                  <td className="border px-2">{p.numero}</td>
                  <td className="border px-2">{currency(p.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="md:w-1/2 flex items-center justify-center text-xl font-bold">
          Total: R$ {currency(totalVenda || total)}
        </div>
      </div>
      <div className="flex gap-2">
        <Button onClick={salvar}>Salvar Negociação</Button>
        <Button variant="secondary" onClick={() => navigate(`/comercial/${id}`)}>
          Cancelar
        </Button>
        <Button variant="secondary" onClick={visualizarOrcamento}>Visualizar Orçamento</Button>
      </div>
    </div>
  );
}

export default Negociacao;
