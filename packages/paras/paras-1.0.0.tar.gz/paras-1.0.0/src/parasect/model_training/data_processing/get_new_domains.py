from argparse import ArgumentParser, Namespace

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select

from parasect.core.parsing import parse_list
from parasect.database.build_database import AdenylationDomain, DomainSynonym


def parse_arguments() -> Namespace:
    """Parse arguments from command line

    :return: Arguments
    :rtype: Namespace
    """
    parser = ArgumentParser(description="Get new domains from database")
    parser.add_argument("-db", '--database', required=True, type=str,
                        help="Path to PARASECT database")
    parser.add_argument("-o", '--out', required=True, type=str,
                        help="Path to output file")
    parser.add_argument("-i", "--input_domains", type=str, required=True,
                        help="Path to file containing identifiers of old domains")

    arguments = parser.parse_args()

    return arguments


def get_domains_without_synonyms(session: Session, excluded_synonyms: list[str]):
    """
    :param session: database session
    :type session: Session
    :param excluded_synonyms: list of domain synonyms
    :type excluded_synonyms: list[str]
    """
    stmt = (
        select(AdenylationDomain)
        .where(
            ~AdenylationDomain.synonyms.any(
                DomainSynonym.synonym.in_(excluded_synonyms)
            )
        )
    )
    return list(session.scalars(stmt).all())


def write_new_domains(session: Session, domain_file: str, out_file: str) -> None:
    """Write domains that are not in domain_file to out_file

    :param session: database session
    :type session: Session
    :param domain_file: path to file containing one domain identifier per line
    :type domain_file: str
    :param out_file: path to output file
    :type out_file: str
    """
    domain_identifiers = parse_list(domain_file)
    domain_synonyms = []
    for domain_identifier in domain_identifiers:
        domain_synonyms.extend(domain_identifier.split('|'))
    domain_synonyms = list(set(domain_synonyms))

    domains = get_domains_without_synonyms(session, domain_synonyms)
    domains.sort(key=lambda x: x.get_name())

    with open(out_file, 'w') as out:
        for domain in domains:
            out.write(f"{domain.get_name()}\n")


def main():
    args = parse_arguments()
    engine = create_engine(f"sqlite:///{args.database}")

    with Session(engine) as session:
        write_new_domains(session, args.input_domains, args.out)


if __name__ == "__main__":
    main()
