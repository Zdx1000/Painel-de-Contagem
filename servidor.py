from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import ceil
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set

from flask import Flask, jsonify, request, send_from_directory
import holidays


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "componentes"

app = Flask(
	__name__,
	static_folder=str(STATIC_DIR),
	static_url_path="",
)


@dataclass
class Configuracoes:
	finalizadoSegundaContagem: int = 0
	finalizadoPrimeiraContagem: int = 0
	itensNovos: int = 0

	@property
	def total(self) -> int:
		return (
			self.finalizadoSegundaContagem
			+ self.finalizadoPrimeiraContagem
			+ self.itensNovos
		)

	def to_dict(self) -> Dict[str, int]:
		return {
			"finalizadoSegundaContagem": self.finalizadoSegundaContagem,
			"finalizadoPrimeiraContagem": self.finalizadoPrimeiraContagem,
			"itensNovos": self.itensNovos,
			"total": self.total,
		}


INTEGER_FIELDS = {
	"totalSkusEstoque",
	"skusRestanteSegunda",
	"skusSegundaConcluida",
	"skusRestantePrimeira",
	"metaContagemDiaria",
	"diasNormal",
	"diasUteis",
	"finalizadoSegundaContagem",
	"finalizadoPrimeiraContagem",
	"itensNovos",
}

FLOAT_FIELDS = {
	"percentualSemContagem",
	"percentualContadoSegunda",
	"percentualSemContagemSegunda",
}


def parse_int(value: Any, *, default: int = 0) -> int:
	try:
		return int(float(value))
	except (TypeError, ValueError):
		return default


def parse_float(value: Any, *, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def parse_iso_date(value: Any) -> Optional[date]:
	if value is None or value == "":
		return None

	if isinstance(value, date):
		return value

	if isinstance(value, datetime):
		return value.date()

	try:
		return datetime.strptime(str(value), "%Y-%m-%d").date()
	except (TypeError, ValueError):
		return None


def build_holiday_set(start_year: int, end_year: int, extra: Iterable[Any]) -> Set[date]:
	years = range(start_year, end_year + 1)
	country_holidays = holidays.country_holidays("BR", years=years)
	holiday_set: Set[date] = set(country_holidays.keys())

	for raw_value in extra:
		parsed = parse_iso_date(raw_value)
		if parsed:
			holiday_set.add(parsed)

	return holiday_set


def calculate_day_differences(
	start: Optional[date],
	end: Optional[date],
	*,
	extra_holidays: Iterable[Any] = (),
) -> Dict[str, int]:
	if not start or not end or end <= start:
		return {"diasNormal": 0, "diasUteis": 0}

	total_days = (end - start).days

	holiday_set = build_holiday_set(start.year, end.year, extra_holidays)

	business_days = 0
	for offset in range(1, total_days + 1):
		current_day = start + timedelta(days=offset)
		if current_day.weekday() >= 5:
			continue
		if current_day in holiday_set:
			continue
		business_days += 1

	return {"diasNormal": total_days, "diasUteis": business_days}


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
	sanitized: Dict[str, Any] = {}
	for key, value in payload.items():
		if key in INTEGER_FIELDS:
			sanitized[key] = parse_int(value)
		elif key in FLOAT_FIELDS:
			sanitized[key] = parse_float(value)
		else:
			sanitized[key] = value
	return sanitized


@app.route("/")
def index() -> Any:
	return send_from_directory(app.static_folder, "index.html")


@app.route("/api/configuracoes", methods=["POST"])
def salvar_configuracoes() -> Any:
	payload = sanitize_payload(request.get_json(force=True) or {})
	configuracoes = Configuracoes(
		finalizadoSegundaContagem=payload.get("finalizadoSegundaContagem", 0),
		finalizadoPrimeiraContagem=payload.get("finalizadoPrimeiraContagem", 0),
		itensNovos=payload.get("itensNovos", 0),
	)

	resposta = {
		"total": configuracoes.total,
		"configuracoes": configuracoes.to_dict(),
		"mensagem": "Configurações calculadas com sucesso",
	}

	print("[CONFIG]", resposta)
	return jsonify(resposta)


@app.route("/api/dashboard", methods=["POST"])
def salvar_dashboard() -> Any:
	payload = request.get_json(force=True) or {}
	metrics = sanitize_payload(payload.get("metrics", {}))
	parameters = sanitize_payload(payload.get("parameters", {}))
	config_payload = sanitize_payload(payload.get("config", {}))

	configuracoes = Configuracoes(
		finalizadoSegundaContagem=config_payload.get("finalizadoSegundaContagem", 0),
		finalizadoPrimeiraContagem=config_payload.get("finalizadoPrimeiraContagem", 0),
		itensNovos=config_payload.get("itensNovos", 0),
	)

	metrics["skusRestanteSegunda"] = (
		configuracoes.finalizadoPrimeiraContagem + configuracoes.itensNovos * 2
	)
	metrics["skusSegundaConcluida"] = configuracoes.finalizadoSegundaContagem
	metrics["totalSkusEstoque"] = configuracoes.total + configuracoes.itensNovos
	metrics["skusRestantePrimeira"] = configuracoes.itensNovos

	data_atualizacao_date = datetime.now().date()
	data_atualizacao = data_atualizacao_date.strftime("%d/%m/%Y")

	previsao_termino = parse_iso_date(metrics.get("previsaoTermino"))

	diferencas = calculate_day_differences(
		start=data_atualizacao_date,
		end=previsao_termino,
		extra_holidays=parameters.get("feriados", ()),
	)

	parameters.update(diferencas)

	dias_uteis = parse_int(parameters.get("diasUteis"))
	meta_contagem_diaria = (
		ceil(metrics["skusRestanteSegunda"] / dias_uteis)
		if dias_uteis
		else 0
	)

	metrics["metaContagemDiaria"] = meta_contagem_diaria

	total_skus = parse_float(metrics.get("totalSkusEstoque"))
	if total_skus > 0:
		percentual_sem_contagem = round(
			(metrics["skusRestanteSegunda"] / total_skus) * 100, 2
		)
		percentual_contado_segunda = round(
			(metrics["skusSegundaConcluida"] / total_skus) * 100, 2
		)
		percentual_sem_contagem_segunda = round(
			(metrics["skusRestantePrimeira"] / total_skus) * 100, 2
		)
	else:
		percentual_sem_contagem = 0.0
		percentual_contado_segunda = 0.0
		percentual_sem_contagem_segunda = 0.0

	metrics["percentualSemContagem"] = percentual_sem_contagem
	metrics["percentualContadoSegunda"] = percentual_contado_segunda
	metrics["percentualSemContagemSegunda"] = percentual_sem_contagem_segunda

	resposta = {
		"status": "ok",
		"mensagem": "Dashboard salvo com sucesso",
		"dataAtualizacao": data_atualizacao,
		"armazem": "CD - UDI",
		"metrics": metrics,
		"configuracoes": configuracoes.to_dict(),
		"parameters": parameters,
	}

	print("[DASHBOARD]", resposta)
	return jsonify(resposta)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)
