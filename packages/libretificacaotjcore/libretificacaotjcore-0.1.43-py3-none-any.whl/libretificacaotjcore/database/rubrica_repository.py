from pymongo.errors import BulkWriteError

class RubricaRepository:
    def __init__(self, db):
        self.__db = db

    async def inserir_rubrica(self, rubrica: dict) -> bool:
        
        try:
            rubricas_no_db = await self.__db.rubricas.find_one(
                {"solicitacaoId": rubrica["solicitacaoId"]}
            )

            if rubricas_no_db is None:
                await self.__db.rubricas.insert_one(rubrica)
                return True

            await self.__db.rubricas.delete_one(
                   {"solicitacaoId": rubrica["solicitacaoId"]}
            )
            await self.__db.rubricas.insert_one(rubrica)
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir o rubrica: {e}")
            return False
        
    async def buscar_por_solicitacao_id(self, solicitacaoId: int) -> list[dict]:
        try:
            return await self.__db.rubricas.find({"solicitacaoId": solicitacaoId}).to_list(length=None)
        except Exception as e:
            print(f"❌ Erro ao buscar rubricas por solicitacaoId: {e}")
            return []